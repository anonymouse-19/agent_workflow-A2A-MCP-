"""
Summarizer Agent — Creates summaries and compiles final reports.

Collects all processed content and analysis results, then produces
a coherent summary using the summarize_text tool.
"""

from .base import BaseAgent


class SummarizerAgent(BaseAgent):

    def __init__(self, bus, tools):
        super().__init__(
            name="summarizer",
            capabilities=["summarization", "reporting", "compilation"],
            bus=bus,
            tools=tools,
        )

    def process(self, message):
        context = message.payload.get("context", {})

        # Collect all text from context
        text = self._assemble_text(context)

        if not text:
            return {"summary": "(No content to summarize)", "method": "none"}

        # A2A: Request keyword analysis directly from analyzer agent
        # (peer-to-peer communication through the MessageBus)
        analysis = {}
        if context:
            keywords_result = self.request("analyzer", {
                "operation": "extract_keywords",
                "context": context,
            })
            if "keywords" in keywords_result:
                analysis["keywords"] = keywords_result

        # Use MCP tool for summarization
        summary_result = self.tools.invoke("summarize_text", {"text": text})

        # Build final report combining summary + A2A analysis
        report = {
            "summary": summary_result.get("summary", ""),
            "method": summary_result.get("method", ""),
            "sentences_selected": summary_result.get("sentences_selected", 0),
        }

        if analysis:
            report["analysis_included"] = list(analysis.keys())
            report["analysis_details"] = analysis

        return report

    def _assemble_text(self, context: dict) -> str:
        """Assemble all readable text from the shared context."""
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
                    lines = []
                    if headers:
                        lines.append(" | ".join(str(h) for h in headers))
                    for row in rows:
                        lines.append(" | ".join(str(v) for v in row))
                    texts.append("\n".join(lines))
        return "\n\n".join(texts)
