"""Tests for the dynamic planner."""

import os
import pytest
import asyncio

os.environ.setdefault("GROQ_API_KEY", "test_key")

from shared.models import AgentCard, ExecutionPlan, PlanStep


def _make_agents():
    return {
        "reader": AgentCard(
            name="reader",
            url="http://localhost:8001",
            description="Reads files",
            capabilities=[{"name": "file_reading"}],
        ),
        "analyzer": AgentCard(
            name="analyzer",
            url="http://localhost:8002",
            description="Analyzes data",
            capabilities=[{"name": "data_analysis"}],
        ),
        "summarizer": AgentCard(
            name="summarizer",
            url="http://localhost:8003",
            description="Summarizes",
            capabilities=[{"name": "text_summarization"}],
        ),
    }


def _make_tools():
    return [
        {"name": "read_text", "description": "Read text file"},
        {"name": "extract_questions", "description": "Extract questions"},
        {"name": "summarize_text", "description": "Summarize text"},
        {"name": "extract_keywords", "description": "Extract keywords"},
        {"name": "analyze_tabular_data", "description": "Analyze tabular data"},
    ]


def test_plan_step_model():
    step = PlanStep(
        step_id="step_1",
        agent="reader",
        tool="read_text",
        inputs={"file_path": "sample.txt"},
        depends_on=[],
        requires_approval=False,
    )
    assert step.step_id == "step_1"
    assert step.agent == "reader"
    assert step.depends_on == []


def test_execution_plan_model():
    steps = [
        PlanStep(step_id="s1", agent="reader", tool="read_text", inputs={}, depends_on=[]),
        PlanStep(step_id="s2", agent="analyzer", tool="extract_questions", inputs={}, depends_on=["s1"]),
    ]
    plan = ExecutionPlan(steps=steps)
    assert len(plan.steps) == 2
    assert plan.steps[1].depends_on == ["s1"]


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY") or os.environ["GROQ_API_KEY"] == "test_key",
    reason="GROQ_API_KEY not set",
)
def test_live_plan_generation():
    from orchestrator.planner import generate_plan
    from shared.llm_adapter import GroqAdapter

    agents = _make_agents()
    tools = _make_tools()
    groq = GroqAdapter()

    plan = asyncio.run(generate_plan(
        goal="Read sample.txt and summarize it",
        agents=agents,
        mcp_tools=tools,
        files=["sample_data/sample.txt"],
        groq=groq,
    ))
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) >= 1
    # First step should be a read
    assert plan.steps[0].tool in ["read_text", "read_pdf", "read_excel"]
