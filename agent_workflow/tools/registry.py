"""
MCP-Style Tool Registry

Tools are registered as independent, self-describing modules.
Agents discover available tools at runtime and decide which to invoke
based on the task context — NOT hardcoded tool calls.

Each tool has:
  - name: unique identifier
  - description: what the tool does (used by agents for selection)
  - input_schema: expected parameters
  - tags: categories for discovery
  - func: the actual callable
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDescriptor:
    """Describes a single MCP tool — agents use this metadata to decide invocation."""
    name: str
    description: str
    input_schema: Dict[str, str]   # param_name → description
    func: Callable
    tags: List[str] = field(default_factory=list)


class ToolRegistry:
    """
    Central registry of all available tools (MCP pattern).
    
    Agents interact with this registry to:
      1. list_tools()    — discover what's available
      2. find_by_tag()   — search tools by capability  
      3. invoke()        — execute a tool by name
    """

    def __init__(self):
        self._tools: Dict[str, ToolDescriptor] = {}

    def register(self, tool: ToolDescriptor):
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their metadata (MCP discovery)."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "tags": t.tags,
            }
            for t in self._tools.values()
        ]

    def get_tool(self, name: str) -> Optional[ToolDescriptor]:
        """Get a specific tool descriptor by name."""
        return self._tools.get(name)

    def invoke(self, name: str, params: Dict[str, Any]) -> Any:
        """Invoke a tool by name with the given parameters."""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Tool '{name}' not found. Available: {list(self._tools.keys())}"}
        try:
            return tool.func(**params)
        except Exception as e:
            return {"error": f"Tool '{name}' failed: {str(e)}"}

    def find_by_tag(self, tag: str) -> List[str]:
        """Find tools matching a capability tag."""
        return [name for name, t in self._tools.items() if tag in t.tags]

    def find_for_task(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Find tools relevant to a task based on keyword matching."""
        results = []
        for t in self._tools.values():
            score = 0
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower in t.name.lower():
                    score += 3
                if kw_lower in t.description.lower():
                    score += 2
                if any(kw_lower in tag.lower() for tag in t.tags):
                    score += 1
            if score > 0:
                results.append({"name": t.name, "description": t.description, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
