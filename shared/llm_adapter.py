"""
Groq-Only LLM Adapter — Wraps the Groq SDK with retry, logging, and rate limit handling.

- Reads GROQ_API_KEY from environment (raises RuntimeError at startup if missing)
- Default model: llama-3.3-70b-versatile
- Fallback on 429: llama3-8b-8192
- Exponential backoff: 2s, 4s, 8s then raise
- Logs every call: model, input tokens, output tokens, latency
"""

import os
import json
import time
import logging
from typing import Any, Dict, List, Optional

from groq import Groq
from groq import RateLimitError

logger = logging.getLogger("groq_adapter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


class GroqAdapter:
    """Groq-only LLM adapter with retry, fallback, and token logging."""

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is required. "
                "Get a free key at https://console.groq.com/keys"
            )
        self.client = Groq(api_key=self.api_key)
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.fallback_model = os.environ.get("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")

        # Cumulative token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def complete(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Dict[str, str]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Groq.

        Args:
            messages: OpenAI-compatible messages [{"role": "...", "content": "..."}]
            response_format: e.g. {"type": "json_object"} for structured output
            temperature: Sampling temperature
            max_tokens: Max output tokens
            model_override: Override the default model for this call

        Returns:
            {
                "content": str,
                "model": str,
                "input_tokens": int,
                "output_tokens": int,
                "latency_ms": float,
            }
        """
        model = model_override or self.model
        backoff_delays = [2, 4, 8]
        last_error = None

        for attempt in range(len(backoff_delays) + 1):
            try:
                start = time.time()
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(**kwargs)
                latency_ms = (time.time() - start) * 1000

                content = response.choices[0].message.content or ""
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0

                # Update cumulative tracking
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_calls += 1

                # Log the call
                logger.info(
                    f"GROQ_CALL model={model} tokens_in={input_tokens} "
                    f"tokens_out={output_tokens} latency={latency_ms:.0f}ms"
                )

                return {
                    "content": content,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "latency_ms": round(latency_ms, 1),
                }

            except RateLimitError as e:
                last_error = e
                if attempt < len(backoff_delays):
                    delay = backoff_delays[attempt]
                    logger.warning(
                        f"Groq rate limit (429) on {model}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{len(backoff_delays)})"
                    )
                    time.sleep(delay)
                    # Switch to fallback model on second retry
                    if attempt >= 1 and model != self.fallback_model:
                        logger.info(f"Switching to fallback model: {self.fallback_model}")
                        model = self.fallback_model
                else:
                    raise RuntimeError(
                        f"Groq rate limit exceeded after {len(backoff_delays)} retries. "
                        f"Last error: {e}"
                    ) from e

        raise RuntimeError(f"Groq request failed: {last_error}")

    def complete_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a completion request expecting JSON output.
        Returns the parsed JSON dict directly.
        """
        result = self.complete(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
            max_tokens=max_tokens,
            model_override=model_override,
        )
        parsed = json.loads(result["content"])
        result["parsed"] = parsed
        return result

    def enhance_clinical(self, text: str, context: str = "") -> Dict[str, Any]:
        """Enhance text with clinical analysis using Groq."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a clinical data analyst assistant. "
                    "Provide concise, evidence-based interpretations. "
                    "Do not make diagnostic claims."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Improve this clinical summary for clarity and add clinical implications.\n\n"
                    f"Context: {context}\n\nSummary: {text}\n\nEnhanced summary:"
                ),
            },
        ]
        return self.complete(messages=messages, temperature=0.3)

    def get_usage(self) -> Dict[str, Any]:
        """Return cumulative token usage stats."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_calls": self.total_calls,
            "estimated_cost_usd": round(
                (self.total_input_tokens * 0.05 / 1_000_000)
                + (self.total_output_tokens * 0.08 / 1_000_000),
                6,
            ),
        }
