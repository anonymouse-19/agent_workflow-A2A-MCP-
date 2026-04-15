"""
Reader Agent — FastAPI microservice (port 8001).

Reads files using MCP tools discovered at runtime.
Exposes A2A agent card at /.well-known/agent.json
"""

import os
import sys
import json
import uuid
import asyncio
import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("reader_agent")

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8004")
AGENT_CARD_PATH = os.path.join(os.path.dirname(__file__), "agent_card.json")
MAX_MCP_RETRIES = 3
MCP_RETRY_DELAY = 2

# File extension to tool name mapping
EXT_TOOL_MAP = {
    ".pdf": "read_pdf",
    ".xlsx": "read_excel",
    ".xls": "read_excel",
    ".txt": "read_text",
    ".csv": "read_text",
    ".md": "read_text",
}


async def _mcp_call(tool_name: str, arguments: dict) -> dict:
    """Connect to MCP server and call a tool."""
    mcp_url = f"{MCP_SERVER_URL}/mcp"
    async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # Parse the result
            for content in result.content:
                if hasattr(content, "text"):
                    try:
                        return json.loads(content.text)
                    except (json.JSONDecodeError, TypeError):
                        return {"content": content.text}
            if hasattr(result, "structuredContent") and result.structuredContent:
                return result.structuredContent
            return {"result": str(result)}


async def _try_mcp_connect():
    """Verify MCP server is reachable with retries."""
    for attempt in range(MAX_MCP_RETRIES):
        try:
            mcp_url = f"{MCP_SERVER_URL}/mcp"
            async with streamable_http_client(mcp_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [t.name for t in tools.tools]
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
    """Startup: verify MCP server is reachable."""
    app.state.mcp_tools = await _try_mcp_connect()
    yield


app = FastAPI(title="Reader Agent", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "reader"}


@app.get("/.well-known/agent.json")
async def agent_card():
    with open(AGENT_CARD_PATH) as f:
        card = json.load(f)
    # Update URL from env
    card["url"] = os.environ.get("READER_AGENT_URL", card.get("url", "http://localhost:8001"))
    return JSONResponse(card)


@app.post("/tasks/send")
async def tasks_send(request: Request):
    """A2A task endpoint — process a file reading task."""
    body = await request.json()
    task_id = body.get("id", str(uuid.uuid4()))
    correlation_id = body.get("correlation_id", str(uuid.uuid4()))
    task_input = body.get("input", {})

    tool_name = task_input.get("tool", "")
    file_path = task_input.get("file_path", "")

    # Dynamic tool selection if not specified
    if not tool_name and file_path:
        ext = os.path.splitext(file_path)[1].lower()
        tool_name = EXT_TOOL_MAP.get(ext, "read_text")

    if not tool_name:
        return JSONResponse({
            "id": task_id,
            "status": "failed",
            "correlation_id": correlation_id,
            "output": None,
            "error": "No tool specified and could not determine from file path",
        })

    logger.info(f"[{correlation_id[:8]}] Executing tool={tool_name} file={file_path}")

    try:
        # Store result in Redis if available
        result = await _mcp_call(tool_name, {"file_path": file_path})

        # Try to store in Redis
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from shared.redis_store import RedisStore
            store = RedisStore()
            await store.connect()
            step_id = task_input.get("step_id", task_id)
            await store.store_result(correlation_id, step_id, result)
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
        logger.error(f"Task failed: {e}")
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
    correlation_id = body.get("correlation_id", str(uuid.uuid4()))
    task_input = body.get("input", {})

    async def event_stream():
        tool_name = task_input.get("tool", "")
        file_path = task_input.get("file_path", "")

        if not tool_name and file_path:
            ext = os.path.splitext(file_path)[1].lower()
            tool_name = EXT_TOOL_MAP.get(ext, "read_text")

        yield f"data: {json.dumps({'id': task_id, 'status': 'in-progress', 'agent': 'reader', 'tool': tool_name})}\n\n"

        try:
            result = await _mcp_call(tool_name, {"file_path": file_path})
            yield f"data: {json.dumps({'id': task_id, 'status': 'completed', 'output': result})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'id': task_id, 'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("READER_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
