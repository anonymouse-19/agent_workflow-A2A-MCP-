"""
Dynamic Planner — sends user goal + agent cards + MCP tools to Groq.
Returns an ExecutionPlan (DAG of PlanSteps).
"""

import asyncio
import json
import logging
from functools import partial
from typing import Dict, List

from shared.llm_adapter import GroqAdapter
from shared.models import AgentCard, ExecutionPlan, PlanStep

logger = logging.getLogger("planner")

PLANNER_SYSTEM_PROMPT = """You are a workflow planner for a healthcare data processing system.
Given a user goal, a list of available agents (with capabilities), and a list of available MCP tools,
produce an execution plan as a JSON object.

Rules:
1. Each step assigns an agent and a tool the agent will call.
2. Steps may depend on earlier steps via "depends_on" (list of step_ids).
3. Independent steps CAN run in parallel (they share no depends_on).
4. If a step involves patient data or critical decisions, set "requires_approval": true.
5. Use ONLY tools and agents that are listed below.
6. Keep plans minimal — do not add unnecessary steps.
7. Each step must have: step_id (string), agent (agent name), tool (MCP tool name), inputs (dict), depends_on (list of step_ids or empty), requires_approval (bool).

Return ONLY a JSON object with this exact schema:
{
  "steps": [
    {
      "step_id": "step_1",
      "agent": "reader",
      "tool": "read_text",
      "inputs": {"file_path": "..."},
      "depends_on": [],
      "requires_approval": false
    }
  ]
}
"""


async def generate_plan(
    goal: str,
    agents: Dict[str, AgentCard],
    mcp_tools: List[dict],
    files: List[str] | None = None,
    groq: GroqAdapter | None = None,
) -> ExecutionPlan:
    """Generate an execution plan via Groq LLM."""
    if groq is None:
        groq = GroqAdapter()

    agents_desc = []
    for name, card in agents.items():
        caps = [
            c.get("name", str(c)) if isinstance(c, dict) else str(c)
            for c in card.capabilities
        ]
        agents_desc.append({"name": name, "capabilities": caps, "description": card.description})

    tools_desc = [{"name": t["name"], "description": t.get("description", "")} for t in mcp_tools]

    user_prompt = f"""Goal: {goal}

Available agents:
{json.dumps(agents_desc, indent=2)}

Available MCP tools:
{json.dumps(tools_desc, indent=2)}

Files provided: {json.dumps(files or [])}

Generate the execution plan now."""

    loop = asyncio.get_event_loop()
    raw_result = await loop.run_in_executor(
        None,
        partial(
            groq.complete_json,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        ),
    )
    plan_raw = raw_result.get("parsed") if raw_result else None

    if plan_raw is None:
        # Retry once
        logger.warning("Planner: first attempt returned None, retrying...")
        raw_result = await loop.run_in_executor(
            None,
            partial(
                groq.complete_json,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            ),
        )
        plan_raw = raw_result.get("parsed") if raw_result else None
        if plan_raw is None:
            raise RuntimeError("Planner failed to produce a valid JSON plan")

    steps = []
    for s in plan_raw.get("steps", []):
        steps.append(PlanStep(
            step_id=s["step_id"],
            agent=s["agent"],
            tool=s["tool"],
            inputs=s.get("inputs", {}),
            depends_on=s.get("depends_on", []),
            requires_approval=s.get("requires_approval", False),
        ))

    plan = ExecutionPlan(steps=steps)
    logger.info(f"Plan generated: {len(plan.steps)} steps")
    for step in plan.steps:
        logger.info(f"  {step.step_id}: agent={step.agent} tool={step.tool} depends={step.depends_on}")
    return plan
