"""
Analyzer Agent — FastAPI microservice (port 8002).

Performs analysis: question extraction, keyword extraction,
tabular data statistics with anomaly detection and trend identification.
Uses MCP tools discovered at runtime. Can delegate to other agents via A2A.
"""

import os
import sys
import json
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("analyzer_agent")

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8004")
AGENT_CARD_PATH = os.path.join(os.path.dirname(__file__), "agent_card.json")
MAX_MCP_RETRIES = 3
MCP_RETRY_DELAY = 2


async def _mcp_call(tool_name: str, arguments: dict) -> dict:
    """Connect to MCP server and call a tool."""
    mcp_url = f"{MCP_SERVER_URL}/mcp"
    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        return json.loads(content.text)
                    except (json.JSONDecodeError, TypeError):
                        return {"content": content.text}
            if hasattr(result, "structuredContent") and result.structuredContent:
                return result.structuredContent
            return {"result": str(result)}


async def _mcp_list_tools() -> list:
    """List available MCP tools."""
    mcp_url = f"{MCP_SERVER_URL}/mcp"
    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            return [{"name": t.name, "description": t.description} for t in tools.tools]


async def _a2a_delegate(agent_url: str, task_input: dict, correlation_id: str) -> dict:
    """Delegate a sub-task to another agent via A2A."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{agent_url}/tasks/send",
            json={
                "id": str(uuid.uuid4()),
                "correlation_id": correlation_id,
                "input": task_input,
            },
        )
        return resp.json()


async def _try_mcp_connect():
    """Verify MCP server is reachable with retries."""
    for attempt in range(MAX_MCP_RETRIES):
        try:
            tools = await _mcp_list_tools()
            tool_names = [t["name"] for t in tools]
            logger.info(f"MCP server connected. Available tools: {tool_names}")
            return tool_names
        except Exception as e:
            logger.warning(f"MCP connect attempt {attempt + 1}/{MAX_MCP_RETRIES} failed: {e}")
            if attempt < MAX_MCP_RETRIES - 1:
                await asyncio.sleep(MCP_RETRY_DELAY)
    logger.error("Failed to connect to MCP server after retries")
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mcp_tools = await _try_mcp_connect()
    yield


app = FastAPI(title="Analyzer Agent", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "analyzer"}


@app.get("/.well-known/agent.json")
async def agent_card():
    with open(AGENT_CARD_PATH) as f:
        card = json.load(f)
    card["url"] = os.environ.get("ANALYZER_AGENT_URL", card.get("url", "http://localhost:8002"))
    return JSONResponse(card)


def _collect_text(context: dict) -> str:
    """Extract text content from context data."""
    texts = []
    for key, data in context.items():
        if not isinstance(data, dict):
            continue
        if "content" in data:
            texts.append(data["content"])
        elif "sheets" in data:
            for sheet_name, sheet in data["sheets"].items():
                headers = sheet.get("headers", [])
                rows = sheet.get("rows", [])
                lines = [f"Sheet: {sheet_name}"]
                if headers:
                    lines.append(" | ".join(str(h) for h in headers))
                for row in rows:
                    lines.append(" | ".join(str(v) for v in row))
                texts.append("\n".join(lines))
    return "\n\n".join(texts)


@app.post("/tasks/send")
async def tasks_send(request: Request):
    """A2A task endpoint — process an analysis task."""
    body = await request.json()
    task_id = body.get("id", str(uuid.uuid4()))
    correlation_id = body.get("correlation_id", str(uuid.uuid4()))
    task_input = body.get("input", {})

    tool_name = task_input.get("tool", "")
    context = task_input.get("context", {})
    operation = task_input.get("operation", tool_name)

    logger.info(f"[{correlation_id[:8]}] Analyzer task: tool={tool_name} operation={operation}")

    try:
        result = {}

        if tool_name == "extract_questions" or operation == "extract_questions":
            text = _collect_text(context) or task_input.get("text", "")
            if text:
                result = await _mcp_call("extract_questions", {"text": text})
            else:
                result = {"questions": [], "count": 0, "note": "No text content found"}

        elif tool_name == "extract_keywords" or operation == "extract_keywords":
            text = _collect_text(context) or task_input.get("text", "")
            if text:
                result = await _mcp_call("extract_keywords", {"text": text})
            else:
                result = {"keywords": [], "note": "No text content found"}

        elif tool_name == "analyze_tabular_data" or operation == "analyze_data":
            # Analyze all tabular data in context
            analysis_results = {}
            for key, data in context.items():
                if not isinstance(data, dict):
                    continue
                if "sheets" in data:
                    for sheet_name, sheet in data["sheets"].items():
                        headers = sheet.get("headers", [])
                        rows = sheet.get("rows", [])
                        if headers and rows:
                            sheet_result = await _mcp_call(
                                "analyze_tabular_data",
                                {"headers": headers, "rows": rows},
                            )
                            analysis_results[sheet_name] = sheet_result
                elif "content" in data:
                    kw_result = await _mcp_call("extract_keywords", {"text": data["content"]})
                    analysis_results[key] = kw_result

            # Try LLM interpretation
            if analysis_results:
                try:
                    llm_result = await _mcp_call(
                        "llm_enhance",
                        {
                            "text": json.dumps(analysis_results, default=str),
                            "context": "Clinical patient data analysis",
                            "task_type": "interpret",
                        },
                    )
                    if "error" not in llm_result:
                        analysis_results["llm_interpretation"] = llm_result.get("enhanced_text", "")
                        analysis_results["groq_model"] = llm_result.get("model", "")
                        analysis_results["tokens_in"] = llm_result.get("input_tokens", 0)
                        analysis_results["tokens_out"] = llm_result.get("output_tokens", 0)
                except Exception as e:
                    logger.warning(f"LLM interpretation skipped: {e}")

            result = analysis_results if analysis_results else {"info": "No analyzable data in context"}

        else:
            result = {"error": f"Unknown tool/operation: {tool_name or operation}"}

        # Store in Redis
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from shared.redis_store import RedisStore
            store = RedisStore()
            await store.connect()
            step_id = task_input.get("step_id", task_id)
            await store.store_result(correlation_id, step_id, result)
            if "tokens_in" in result:
                await store.store_token_usage(
                    correlation_id,
                    result.get("tokens_in", 0),
                    result.get("tokens_out", 0),
                )
            await store.close()
        except Exception as e:
            logger.warning(f"Redis store failed (non-fatal): {e}")

        return JSONResponse({
            "id": task_id,
            "status": "completed",
            "correlation_id": correlation_id,
            "output": result,
            "error": None,
        })
    except Exception as e:
        logger.error(f"Analyzer task failed: {e}")
        return JSONResponse({
            "id": task_id,
            "status": "failed",
            "correlation_id": correlation_id,
            "output": None,
            "error": str(e),
        })


@app.post("/tasks/stream")
async def tasks_stream(request: Request):
    """A2A streaming endpoint via SSE."""
    body = await request.json()
    task_id = body.get("id", str(uuid.uuid4()))
    task_input = body.get("input", {})
    tool_name = task_input.get("tool", task_input.get("operation", "analyze"))

    async def event_stream():
        yield f"data: {json.dumps({'id': task_id, 'status': 'in-progress', 'agent': 'analyzer', 'tool': tool_name})}\n\n"
        try:
            # Re-process the same as tasks/send
            resp = await tasks_send(request)
            result = json.loads(resp.body)
            yield f"data: {json.dumps({'id': task_id, 'status': result.get('status', 'completed'), 'output': result.get('output')})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'id': task_id, 'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("ANALYZER_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
