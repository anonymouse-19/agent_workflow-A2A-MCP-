"""Tests for Groq adapter."""

import os
import pytest
import asyncio

# Set a dummy key for tests that mock
os.environ.setdefault("GROQ_API_KEY", "test_key")

from shared.llm_adapter import GroqAdapter


def test_adapter_creation():
    adapter = GroqAdapter()
    assert adapter.model == os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    assert adapter.total_calls == 0
    assert adapter.total_input_tokens == 0
    assert adapter.total_output_tokens == 0


def test_get_usage():
    adapter = GroqAdapter()
    adapter.total_input_tokens = 100
    adapter.total_output_tokens = 50
    adapter.total_calls = 3
    usage = adapter.get_usage()
    assert usage["total_input_tokens"] == 100
    assert usage["total_output_tokens"] == 50
    assert usage["total_calls"] == 3
    assert "estimated_cost_usd" in usage


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY") or os.environ["GROQ_API_KEY"] == "test_key",
    reason="GROQ_API_KEY not set",
)
def test_live_completion():
    adapter = GroqAdapter()
    result = asyncio.run(adapter.complete(
        messages=[{"role": "user", "content": "Say hello in one word."}],
        max_tokens=10,
    ))
    assert isinstance(result, str)
    assert len(result) > 0
    assert adapter.total_calls == 1


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY") or os.environ["GROQ_API_KEY"] == "test_key",
    reason="GROQ_API_KEY not set",
)
def test_live_json_completion():
    adapter = GroqAdapter()
    result = asyncio.run(adapter.complete_json(
        messages=[{"role": "user", "content": 'Return a JSON object with key "status" and value "ok".'}],
    ))
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
