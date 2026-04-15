"""
Reader Agent — Reads files using MCP tools.

The Reader agent selects the appropriate read tool based on file type.
If the planner specifies a tool, it uses that. Otherwise, it dynamically
picks from the registry based on file extension.
"""

import os
from .base import BaseAgent


class ReaderAgent(BaseAgent):

    def __init__(self, bus, tools):
        super().__init__(
            name="reader",
            capabilities=["file_reading", "pdf", "excel", "text"],
            bus=bus,
            tools=tools,
        )
        # Maps file extensions to tool names (used for dynamic selection)
        self._ext_map = {
            ".pdf": "read_pdf",
            ".xlsx": "read_excel",
            ".xls": "read_excel",
            ".txt": "read_text",
            ".csv": "read_text",
            ".md": "read_text",
        }

    def process(self, message):
        params = message.payload
        tool_name = params.get("tool")
        file_path = params.get("file_path", "")

        # MCP-style: if no tool specified, agent decides dynamically
        if not tool_name:
            ext = os.path.splitext(file_path)[1].lower()
            tool_name = self._ext_map.get(ext)
            if not tool_name:
                # Fallback: query registry
                tool_name = self.select_tool(ext.replace(".", "")) or "read_text"

        result = self.tools.invoke(tool_name, {"file_path": file_path})
        return result
