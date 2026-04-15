"""Tests for the orchestrator — agent registry and workflow logic."""

import os
import pytest
import asyncio

os.environ.setdefault("GROQ_API_KEY", "test_key")

from shared.models import AgentCard, PlanStep, ExecutionPlan


def test_agent_card_model():
    card = AgentCard(
        name="test-agent",
        url="http://localhost:9999",
        description="A test agent",
        capabilities=[{"name": "test_cap"}],
    )
    assert card.name == "test-agent"
    assert card.url == "http://localhost:9999"
    assert len(card.capabilities) == 1


def test_find_by_capability():
    from orchestrator.agent_registry import AgentRegistry

    registry = AgentRegistry(agent_urls=[])
    # Manually add agents
    registry._agents["reader"] = AgentCard(
        name="reader",
        url="http://localhost:8001",
        description="Reads files",
        capabilities=[{"name": "file_reading"}, {"name": "pdf_reading"}],
    )
    registry._agents["analyzer"] = AgentCard(
        name="analyzer",
        url="http://localhost:8002",
        description="Analyzes data",
        capabilities=[{"name": "data_analysis"}],
    )

    matches = registry.find_by_capability("file_reading")
    assert len(matches) == 1
    assert matches[0].name == "reader"

    matches = registry.find_by_capability("data")
    assert len(matches) == 1
    assert matches[0].name == "analyzer"

    matches = registry.find_by_capability("nonexistent")
    assert len(matches) == 0


def test_get_agent():
    from orchestrator.agent_registry import AgentRegistry

    registry = AgentRegistry(agent_urls=[])
    registry._agents["reader"] = AgentCard(
        name="reader",
        url="http://localhost:8001",
        description="Reads files",
        capabilities=[{"name": "file_reading"}],
    )
    assert registry.get_agent("reader") is not None
    assert registry.get_agent("nonexistent") is None


def test_dag_ordering():
    """Verify DAG dependency resolution logic."""
    steps = [
        PlanStep(step_id="s1", agent="reader", tool="read_text", inputs={}, depends_on=[]),
        PlanStep(step_id="s2", agent="analyzer", tool="extract_questions", inputs={}, depends_on=["s1"]),
        PlanStep(step_id="s3", agent="analyzer", tool="extract_keywords", inputs={}, depends_on=["s1"]),
        PlanStep(step_id="s4", agent="summarizer", tool="summarize_text", inputs={}, depends_on=["s2", "s3"]),
    ]
    plan = ExecutionPlan(steps=steps)

    # Simulate DAG resolution
    all_steps = {s.step_id: s for s in plan.steps}
    completed = set()
    execution_order = []

    remaining = set(all_steps.keys())
    while remaining:
        ready = [
            sid for sid in remaining
            if all(d in completed for d in all_steps[sid].depends_on)
        ]
        assert len(ready) > 0, "Deadlock detected"
        execution_order.append(sorted(ready))
        for sid in ready:
            completed.add(sid)
            remaining.discard(sid)

    # Round 1: s1 (no deps)
    assert execution_order[0] == ["s1"]
    # Round 2: s2 and s3 (both depend on s1, can run in parallel)
    assert sorted(execution_order[1]) == ["s2", "s3"]
    # Round 3: s4 (depends on s2 and s3)
    assert execution_order[2] == ["s4"]
