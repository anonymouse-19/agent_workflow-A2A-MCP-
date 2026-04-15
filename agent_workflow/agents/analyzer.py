"""
Analyzer Agent — Performs analysis operations on content.

Dynamically decides which analysis tool to use based on the operation
requested and the data available in the context. Handles:
  - Question extraction from text
  - Keyword extraction
  - Tabular data analysis (statistics, insights)
"""

from collections import Counter
from .base import BaseAgent


class AnalyzerAgent(BaseAgent):

    def __init__(self, bus, tools):
        super().__init__(
            name="analyzer",
            capabilities=["analysis", "extraction", "questions", "keywords", "statistics"],
            bus=bus,
            tools=tools,
        )

    def process(self, message):
        operation = message.payload.get("operation", "")
        context = message.payload.get("context", {})

        if operation == "extract_questions":
            text = self._collect_text(context)
            if not text:
                return {"questions": [], "count": 0, "note": "No text content found"}
            return self.tools.invoke("extract_questions", {"text": text})

        elif operation == "analyze_data":
            return self._analyze(context)

        elif operation == "extract_keywords":
            text = self._collect_text(context)
            if not text:
                return {"keywords": [], "note": "No text content found"}
            return self.tools.invoke("extract_keywords", {"text": text})

        return {"error": f"Unknown operation: {operation}"}

    def _collect_text(self, context: dict) -> str:
        """Extract all text content from the shared context."""
        texts = []
        for key, data in context.items():
            if not isinstance(data, dict):
                continue
            if "content" in data:
                texts.append(data["content"])
            elif "sheets" in data:
                # Convert tabular data to text for text-based analysis
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

    def _analyze(self, context: dict) -> dict:
        """Run analysis — picks the right tool based on data type."""
        results = {}

        for key, data in context.items():
            if not isinstance(data, dict):
                continue

            if "sheets" in data:
                # Tabular data → use analyze_tabular_data tool
                for sheet_name, sheet in data["sheets"].items():
                    result = self.tools.invoke("analyze_tabular_data", {
                        "headers": sheet.get("headers", []),
                        "rows": sheet.get("rows", []),
                    })
                    results[f"{sheet_name}"] = result

            elif "content" in data:
                # Text data → use keyword extraction as analysis
                result = self.tools.invoke("extract_keywords", {"text": data["content"]})
                results[key] = result

        if not results:
            return {"info": "No analyzable data found in context"}
        return results
