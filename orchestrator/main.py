"""
Orchestrator — FastAPI app (port 8000).

1. Discovers agents and MCP tools.
2. Sends goal to planner (Groq) to get an ExecutionPlan.
3. Executes steps in DAG order with parallel asyncio.gather().
4. Provides SSE stream for live trace.
5. Supports human-in-the-loop approval for flagged steps.
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Dict

import httpx
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import (
    A2ATask, ExecutionPlan, PlanStep, TaskStatus,
    TraceEvent, TokenUsage, WorkflowRequest, StepApproval,
)
from shared.llm_adapter import GroqAdapter
from shared.redis_store import RedisStore
from orchestrator.agent_registry import AgentRegistry
from orchestrator.planner import generate_plan

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("orchestrator")

# Pending approvals: correlation_id → {step_id: asyncio.Event}
pending_approvals: Dict[str, Dict[str, asyncio.Event]] = {}
approval_decisions: Dict[str, Dict[str, bool]] = {}

# Active workflow traces: correlation_id → list of TraceEvents
active_traces: Dict[str, list] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Discover agents and MCP tools at startup
    registry = AgentRegistry()
    agents = await registry.discover()
    mcp_tools = await registry.get_mcp_tools()

    app.state.registry = registry
    app.state.agents = agents
    app.state.mcp_tools = mcp_tools
    app.state.groq = GroqAdapter()

    redis = RedisStore()
    await redis.connect()
    app.state.redis = redis

    logger.info(f"Orchestrator ready: {len(agents)} agents, {len(mcp_tools)} MCP tools")
    yield

    await redis.close()


app = FastAPI(title="Healthcare Multi-Agent Orchestrator", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "orchestrator"}


@app.get("/agents")
async def list_agents():
    """Return discovered agent cards."""
    agents = app.state.registry.get_all()
    return {name: {"url": a.url, "description": a.description} for name, a in agents.items()}


@app.get("/tools")
async def list_tools():
    """Return discovered MCP tools."""
    return app.state.mcp_tools


UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return its server-side path."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    # Sanitize filename — keep only the basename
    safe_name = os.path.basename(file.filename or "upload")
    dest = os.path.join(UPLOAD_DIR, safe_name)

    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    logger.info(f"Uploaded file: {safe_name} ({len(contents)} bytes)")
    return {"filename": safe_name, "path": f"uploads/{safe_name}", "size": len(contents)}


async def _execute_step(
    step: PlanStep,
    correlation_id: str,
    results: dict,
    trace: list,
    groq: GroqAdapter,
    redis: RedisStore,
    agents: dict,
) -> dict:
    """Execute a single plan step by delegating to an A2A agent."""
    step_trace = TraceEvent(
        agent=step.agent,
        tool=step.tool,
        status="in-progress",
        detail=f"Starting step {step.step_id}",
        step_id=step.step_id,
        correlation_id=correlation_id,
    )
    trace.append(step_trace.model_dump())

    agent_card = agents.get(step.agent)
    if not agent_card:
        error_msg = f"Agent '{step.agent}' not found in registry"
        trace.append(TraceEvent(
            agent=step.agent, tool=step.tool, status="failed",
            detail=error_msg, step_id=step.step_id, correlation_id=correlation_id,
        ).model_dump())
        return {"error": error_msg}

    # Build context from dependent steps
    context = {}
    for dep_id in step.depends_on:
        if dep_id in results:
            context[dep_id] = results[dep_id]

    task_input = {
        **step.inputs,
        "tool": step.tool,
        "step_id": step.step_id,
        "context": context,
    }

    if context:
        task_input["analysis"] = {k: v for k, v in context.items() if isinstance(v, dict)}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{agent_card.url}/tasks/send",
                json={
                    "id": str(uuid.uuid4()),
                    "correlation_id": correlation_id,
                    "input": task_input,
                },
            )
            result = resp.json()

        output = result.get("output", {})
        status = result.get("status", "completed")

        # Track tokens
        if isinstance(output, dict) and "tokens_in" in output:
            groq.total_input_tokens += output.get("tokens_in", 0)
            groq.total_output_tokens += output.get("tokens_out", 0)

        trace.append(TraceEvent(
            agent=step.agent, tool=step.tool, status=status,
            detail=f"Step {step.step_id} {status}",
            step_id=step.step_id, correlation_id=correlation_id,
            groq_model=output.get("groq_model") if isinstance(output, dict) else None,
            tokens_in=output.get("tokens_in", 0) if isinstance(output, dict) else 0,
            tokens_out=output.get("tokens_out", 0) if isinstance(output, dict) else 0,
        ).model_dump())

        logger.info(f"[{correlation_id[:8]}] _execute_step {step.step_id} returning, status={status}")
        return output
    except Exception as e:
        logger.error(f"Step {step.step_id} failed: {e}", exc_info=True)
        trace.append(TraceEvent(
            agent=step.agent, tool=step.tool, status="failed",
            detail=str(e), step_id=step.step_id, correlation_id=correlation_id,
        ).model_dump())
        return {"error": str(e)}


async def _run_workflow(
    plan: ExecutionPlan,
    correlation_id: str,
    groq: GroqAdapter,
    redis: RedisStore,
    agents: dict,
) -> dict:
    """Execute the plan as a DAG with parallel execution."""
    results: Dict[str, dict] = {}
    trace: list = []
    active_traces[correlation_id] = trace
    completed_steps = set()

    # Build dependency graph
    all_steps = {s.step_id: s for s in plan.steps}
    remaining = set(all_steps.keys())

    while remaining:
        # Find steps whose dependencies are all completed
        logger.info(f"[{correlation_id[:8]}] Loop: remaining={remaining}, completed={completed_steps}")
        ready = []
        for sid in remaining:
            step = all_steps[sid]
            deps_met = all(d in completed_steps for d in step.depends_on)
            logger.info(f"[{correlation_id[:8]}]   {sid}: depends={step.depends_on} met={deps_met}")
            if deps_met:
                ready.append(step)

        if not ready:
            logger.error(f"Deadlock: no steps ready. Remaining: {remaining}")
            break

        logger.info(f"[{correlation_id[:8]}] Ready steps: {[s.step_id for s in ready]}")

        # Check for approval-required steps
        for step in ready:
            if step.requires_approval:
                trace.append(TraceEvent(
                    agent=step.agent, tool=step.tool, status="requires-approval",
                    detail=f"Step {step.step_id} requires human approval",
                    step_id=step.step_id, correlation_id=correlation_id,
                ).model_dump())

                if correlation_id not in pending_approvals:
                    pending_approvals[correlation_id] = {}
                    approval_decisions[correlation_id] = {}
                event = asyncio.Event()
                pending_approvals[correlation_id][step.step_id] = event

                # Wait for approval (timeout 5 min)
                try:
                    await asyncio.wait_for(event.wait(), timeout=300)
                except asyncio.TimeoutError:
                    logger.warning(f"Approval timeout for {step.step_id}")

                approved = approval_decisions.get(correlation_id, {}).get(step.step_id, True)
                if not approved:
                    trace.append(TraceEvent(
                        agent=step.agent, tool=step.tool, status="failed",
                        detail=f"Step {step.step_id} rejected by user",
                        step_id=step.step_id, correlation_id=correlation_id,
                    ).model_dump())
                    completed_steps.add(step.step_id)
                    remaining.discard(step.step_id)
                    results[step.step_id] = {"error": "Rejected by user"}
                    continue

        # Execute ready steps in parallel
        executable = [s for s in ready if s.step_id in remaining]
        logger.info(f"[{correlation_id[:8]}] Executing {len(executable)} steps: {[s.step_id for s in executable]}")
        tasks = [
            _execute_step(s, correlation_id, results, trace, groq, redis, agents)
            for s in executable
        ]
        step_results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"[{correlation_id[:8]}] gather returned {len(step_results)} results")

        for step, result in zip(executable, step_results):
            if isinstance(result, Exception):
                logger.error(f"[{correlation_id[:8]}] Step {step.step_id} exception: {result}")
                results[step.step_id] = {"error": str(result)}
            else:
                logger.info(f"[{correlation_id[:8]}] Step {step.step_id} completed, output type={type(result).__name__}")
                results[step.step_id] = result
            completed_steps.add(step.step_id)
            remaining.discard(step.step_id)

    # Store final results
    try:
        await redis.store_result(correlation_id, "final", results)
    except Exception as e:
        logger.warning(f"Redis final store failed: {e}")

    # Token usage summary
    usage = TokenUsage(
        total_input_tokens=groq.total_input_tokens,
        total_output_tokens=groq.total_output_tokens,
        total_calls=groq.total_calls,
    )

    return {
        "correlation_id": correlation_id,
        "status": "completed",
        "results": results,
        "trace": trace,
        "token_usage": usage.model_dump(),
    }


@app.post("/workflow")
async def start_workflow(req: WorkflowRequest):
    """Start a new workflow: plan + execute."""
    correlation_id = req.correlation_id or str(uuid.uuid4())
    logger.info(f"[{correlation_id[:8]}] Workflow: {req.goal}")

    groq = app.state.groq
    redis = app.state.redis
    agents = app.state.agents
    mcp_tools = app.state.mcp_tools

    # Generate plan
    plan = await generate_plan(
        goal=req.goal,
        agents=agents,
        mcp_tools=mcp_tools,
        files=req.files,
        groq=groq,
    )

    # Execute plan
    result = await _run_workflow(plan, correlation_id, groq, redis, agents)
    result["plan"] = [s.model_dump() for s in plan.steps]

    return JSONResponse(result)


@app.post("/workflow/stream")
async def stream_workflow(request: Request):
    """Start workflow and stream trace events via SSE."""
    body = await request.json()
    req = WorkflowRequest(**body)
    correlation_id = req.correlation_id or str(uuid.uuid4())

    groq = app.state.groq
    redis = app.state.redis
    agents = app.state.agents
    mcp_tools = app.state.mcp_tools

    async def event_gen():
        yield f"data: {json.dumps({'type': 'start', 'correlation_id': correlation_id})}\n\n"

        # Plan
        try:
            plan = await generate_plan(
                goal=req.goal,
                agents=agents,
                mcp_tools=mcp_tools,
                files=req.files,
                groq=groq,
            )
            yield f"data: {json.dumps({'type': 'plan', 'steps': [s.model_dump() for s in plan.steps]})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
            return

        # Execute with streaming trace
        trace: list = []
        active_traces[correlation_id] = trace
        results: Dict[str, dict] = {}
        completed_steps = set()
        all_steps = {s.step_id: s for s in plan.steps}
        remaining = set(all_steps.keys())

        while remaining:
            ready = []
            for sid in remaining:
                step = all_steps[sid]
                if all(d in completed_steps for d in step.depends_on):
                    ready.append(step)
            if not ready:
                yield f"data: {json.dumps({'type': 'error', 'detail': 'Deadlock in plan execution'})}\n\n"
                break

            for step in ready:
                yield f"data: {json.dumps({'type': 'trace', 'step_id': step.step_id, 'agent': step.agent, 'tool': step.tool, 'status': 'in-progress'})}\n\n"

            executable = [s for s in ready if s.step_id in remaining]
            tasks = [
                _execute_step(s, correlation_id, results, trace, groq, redis, agents)
                for s in executable
            ]
            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, result in zip(executable, step_results):
                if isinstance(result, Exception):
                    results[step.step_id] = {"error": str(result)}
                    status = "failed"
                else:
                    results[step.step_id] = result
                    status = "completed"
                completed_steps.add(step.step_id)
                remaining.discard(step.step_id)
                yield f"data: {json.dumps({'type': 'trace', 'step_id': step.step_id, 'agent': step.agent, 'tool': step.tool, 'status': status})}\n\n"

        usage = TokenUsage(
            total_input_tokens=groq.total_input_tokens,
            total_output_tokens=groq.total_output_tokens,
            total_calls=groq.total_calls,
        )
        yield f"data: {json.dumps({'type': 'complete', 'results': results, 'token_usage': usage.model_dump()}, default=str)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/workflow/approve")
async def approve_step(approval: StepApproval):
    """Approve or reject a pending step."""
    cid = approval.correlation_id
    sid = approval.step_id
    if cid in pending_approvals and sid in pending_approvals[cid]:
        approval_decisions.setdefault(cid, {})[sid] = approval.approved
        pending_approvals[cid][sid].set()
        return {"status": "ok", "step_id": sid, "approved": approval.approved}
    return JSONResponse({"error": "No pending approval found"}, status_code=404)


@app.get("/workflow/{correlation_id}/trace")
async def get_trace(correlation_id: str):
    """Get trace events for a workflow."""
    trace = active_traces.get(correlation_id, [])
    return {"correlation_id": correlation_id, "trace": trace}


@app.get("/workflow/{correlation_id}/results")
async def get_results(correlation_id: str):
    """Get stored results from Redis."""
    redis = app.state.redis
    try:
        results = await redis.get_all_results(correlation_id)
        usage = await redis.get_token_usage(correlation_id)
        return {"correlation_id": correlation_id, "results": results, "token_usage": usage}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ORCHESTRATOR_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
