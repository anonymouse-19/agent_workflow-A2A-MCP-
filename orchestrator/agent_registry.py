"""
Agent Registry — discovers agents by fetching their A2A Agent Cards.
"""

import asyncio
import logging
from typing import Dict, List, Optional

import httpx

from shared.models import AgentCard

logger = logging.getLogger("agent_registry")

DEFAULT_AGENT_URLS = [
    "http://localhost:8001",
    "http://localhost:8002",
    "http://localhost:8003",
]


class AgentRegistry:
    """Discovers and caches A2A agent cards."""

    def __init__(self, agent_urls: Optional[List[str]] = None):
        self._urls = agent_urls or [
            u.strip() for u in
            __import__("os").environ.get("AGENT_URLS", ",".join(DEFAULT_AGENT_URLS)).split(",")
            if u.strip()
        ]
        self._agents: Dict[str, AgentCard] = {}

    async def discover(self) -> Dict[str, AgentCard]:
        """Fetch agent cards from all configured URLs."""
        tasks = [self._fetch_card(url) for url in self._urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, AgentCard):
                self._agents[result.name] = result
                logger.info(f"Discovered agent: {result.name} at {result.url}")
            elif isinstance(result, Exception):
                logger.warning(f"Agent discovery failed: {result}")
        logger.info(f"Registry: {len(self._agents)} agents discovered")
        return self._agents

    async def _fetch_card(self, url: str) -> AgentCard:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{url}/.well-known/agent.json")
            resp.raise_for_status()
            data = resp.json()
            return AgentCard(
                name=data["name"],
                url=data.get("url", url),
                description=data.get("description", ""),
                capabilities=[
                    {"name": c} if isinstance(c, str) else c
                    for c in data.get("capabilities", [])
                ],
                inputModes=data.get("inputModes", ["text/plain"]),
                outputModes=data.get("outputModes", ["application/json"]),
            )

    def get_agent(self, name: str) -> Optional[AgentCard]:
        return self._agents.get(name)

    def get_all(self) -> Dict[str, AgentCard]:
        return dict(self._agents)

    def find_by_capability(self, capability: str) -> List[AgentCard]:
        """Find agents that have a specific capability."""
        matches = []
        for agent in self._agents.values():
            for cap in agent.capabilities:
                cap_name = cap.get("name", "") if isinstance(cap, dict) else str(cap)
                if capability.lower() in cap_name.lower():
                    matches.append(agent)
                    break
        return matches

    async def get_mcp_tools(self) -> List[dict]:
        """Discover MCP tools from the MCP server."""
        mcp_url = __import__("os").environ.get("MCP_SERVER_URL", "http://localhost:8004")
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamable_http_client

            async with streamable_http_client(f"{mcp_url}/mcp") as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    tools = []
                    for t in result.tools:
                        tools.append({
                            "name": t.name,
                            "description": t.description or "",
                            "parameters": t.inputSchema if hasattr(t, "inputSchema") else {},
                        })
                    logger.info(f"MCP tools discovered: {[t['name'] for t in tools]}")
                    return tools
        except Exception as e:
            logger.error(f"MCP tool discovery failed: {e}")
            return []
