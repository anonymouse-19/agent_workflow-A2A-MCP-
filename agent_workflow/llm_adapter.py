"""
LLM Adapter — Pluggable AI backend for the Agent Workflow System.

Supports three backends:
  - "openai"  : Uses OpenAI API (requires OPENAI_API_KEY env var)
  - "ollama"  : Uses a local Ollama server (requires ollama running)
  - "mock"    : Algorithmic fallback — no API calls, zero cost

The system works fully in mock mode. When an LLM is available,
it enhances summaries, generates richer insights, and provides
natural-language clinical interpretations.

Usage:
  adapter = LLMAdapter()                     # auto-detects or defaults to mock
  adapter = LLMAdapter(backend="openai")     # force OpenAI
  adapter = LLMAdapter(backend="mock")       # force mock
"""

import os
import re
from collections import Counter


class LLMAdapter:
    """Pluggable LLM backend with automatic fallback to mock."""

    def __init__(self, backend: str = "auto"):
        """
        Initialize the adapter.

        Args:
            backend: "openai", "ollama", "mock", or "auto" (tries openai → ollama → mock)
        """
        self._backend = self._resolve_backend(backend)

    @property
    def backend_name(self) -> str:
        return self._backend

    def _resolve_backend(self, requested: str) -> str:
        """Determine which backend to use."""
        if requested == "openai":
            if os.environ.get("OPENAI_API_KEY"):
                return "openai"
            print("  [LLM] OPENAI_API_KEY not set — falling back to mock")
            return "mock"

        if requested == "ollama":
            if self._check_ollama():
                return "ollama"
            print("  [LLM] Ollama not available — falling back to mock")
            return "mock"

        if requested == "mock":
            return "mock"

        # Auto-detect
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if self._check_ollama():
            return "ollama"
        return "mock"

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:11434/api/tags",
                method="GET",
            )
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            return False

    # ── Public API ────────────────────────────────────────────────────────

    def complete(self, prompt: str, system: str = "", max_tokens: int = 500) -> str:
        """Send a completion request to the configured backend."""
        if self._backend == "openai":
            return self._openai_complete(prompt, system, max_tokens)
        elif self._backend == "ollama":
            return self._ollama_complete(prompt, system, max_tokens)
        else:
            return self._mock_complete(prompt, system)

    def enhance_summary(self, summary: str, context: str = "") -> str:
        """Enhance an extractive summary with LLM-generated improvements."""
        prompt = (
            f"You are a clinical data analyst. Improve this summary for clarity "
            f"and add any clinical implications:\n\n"
            f"Context: {context}\n\n"
            f"Summary: {summary}\n\n"
            f"Enhanced summary:"
        )
        return self.complete(prompt, system="You are a healthcare AI assistant.")

    def generate_insights(self, data_stats: dict) -> list:
        """Generate clinical insights from statistical data."""
        prompt = (
            f"Given the following patient data statistics, provide 3-5 clinical insights "
            f"and actionable recommendations:\n\n{data_stats}\n\nInsights:"
        )
        response = self.complete(prompt, system="You are a clinical data analyst.")
        # Split response into individual insights
        insights = [line.strip().lstrip("0123456789.-) ")
                     for line in response.split("\n")
                     if line.strip() and len(line.strip()) > 10]
        return insights if insights else [response]

    # ── Backend Implementations ───────────────────────────────────────────

    def _openai_complete(self, prompt: str, system: str, max_tokens: int) -> str:
        """Call OpenAI API."""
        import json
        import urllib.request

        api_key = os.environ["OPENAI_API_KEY"]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()

    def _ollama_complete(self, prompt: str, system: str, max_tokens: int) -> str:
        """Call local Ollama server."""
        import json
        import urllib.request

        body = json.dumps({
            "model": "llama3",
            "prompt": f"{system}\n\n{prompt}" if system else prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
        return result.get("response", "").strip()

    def _mock_complete(self, prompt: str, system: str) -> str:
        """
        Algorithmic mock — generates plausible responses without any API.
        Uses keyword analysis and template-based generation.
        """
        prompt_lower = prompt.lower()

        # Clinical summary enhancement
        if "summary" in prompt_lower or "enhance" in prompt_lower or "improve" in prompt_lower:
            return self._mock_enhance_summary(prompt)

        # Insight generation
        if "insight" in prompt_lower or "recommend" in prompt_lower:
            return self._mock_generate_insights(prompt)

        # Default: keyword-based response
        return self._mock_general(prompt)

    def _mock_enhance_summary(self, prompt: str) -> str:
        """Generate a mock-enhanced summary using text analysis."""
        # Extract the original summary from the prompt
        parts = prompt.split("Summary:")
        original = parts[-1].strip() if len(parts) > 1 else prompt

        # Clean and split into key points
        sentences = re.split(r'(?<=[.!])\s+', original)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        enhanced_parts = []
        enhanced_parts.append("[Clinical Analysis] " + sentences[0] if sentences else "")

        if len(sentences) > 1:
            enhanced_parts.append(
                "This finding has significant implications for patient care workflows "
                "and clinical decision support systems."
            )
            for s in sentences[1:]:
                enhanced_parts.append(s)

        enhanced_parts.append(
            "These results suggest prioritizing AI-assisted diagnostics in departments "
            "with high patient volumes and time-critical decision requirements."
        )

        return " ".join(p for p in enhanced_parts if p)

    def _mock_generate_insights(self, prompt: str) -> str:
        """Generate mock clinical insights from data context."""
        insights = []

        if "heart_rate" in prompt.lower() or "bpm" in prompt.lower():
            insights.append(
                "Heart rate variability across the patient cohort suggests "
                "monitoring protocols should be adjusted for high-risk groups"
            )
        if "spo2" in prompt.lower():
            insights.append(
                "SpO2 readings below 94% in ICU patients warrant immediate "
                "escalation — consider automated alert thresholds"
            )
        if "risk" in prompt.lower() or "critical" in prompt.lower():
            insights.append(
                "25% of patients are classified as Critical risk — resource "
                "allocation should prioritize ICU staffing and device availability"
            )

        # Always add general insights
        insights.extend([
            "Recommend implementing predictive models for early deterioration "
            "detection based on vital sign trend analysis",
            "Cross-department data sharing could improve continuity of care "
            "for patients transitioning between General and ICU wards",
        ])

        return "\n".join(f"{i+1}. {insight}" for i, insight in enumerate(insights))

    def _mock_general(self, prompt: str) -> str:
        """General mock response based on keyword matching."""
        words = re.findall(r'\b[a-z]{4,}\b', prompt.lower())
        freq = Counter(words)
        top_words = [w for w, _ in freq.most_common(5)]

        return (
            f"Analysis complete. Key topics identified: {', '.join(top_words)}. "
            f"Recommend further investigation of clinical correlations and "
            f"integration with existing Philips IntelliSpace workflows."
        )
