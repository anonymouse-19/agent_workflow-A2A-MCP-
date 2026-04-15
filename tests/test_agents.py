"""
Unit tests for the Agent Workflow System.

Run:
  python -m pytest tests/ -v
  # or without pytest:
  python -m unittest tests.test_agents -v
"""

import os
import sys
import unittest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_workflow.core.message_bus import MessageBus
from agent_workflow.core.models import Message, MessageType, Step, ExecutionPlan
from agent_workflow.tools.registry import ToolRegistry, ToolDescriptor
from agent_workflow.tools.text_tool import (
    read_text, extract_questions, summarize_text,
    extract_keywords, analyze_tabular_data,
)
from agent_workflow.llm_adapter import LLMAdapter
from agent_workflow.agents.planner import PlannerAgent
from agent_workflow.agents.reader import ReaderAgent
from agent_workflow.agents.analyzer import AnalyzerAgent
from agent_workflow.agents.summarizer import SummarizerAgent
from agent_workflow.main import build_tool_registry, setup


# ── Message Bus Tests ────────────────────────────────────────────────────────

class TestMessageBus(unittest.TestCase):
    """Test A2A message routing via the MessageBus."""

    def test_send_and_receive(self):
        bus = MessageBus()
        bus.register_agent("agent_a")
        bus.register_agent("agent_b")

        msg = Message(
            sender="agent_a",
            recipient="agent_b",
            msg_type=MessageType.REQUEST,
            payload={"data": "hello"},
        )
        bus.send(msg)

        received = bus.receive("agent_b")
        self.assertIsNotNone(received)
        self.assertEqual(received.payload["data"], "hello")
        self.assertEqual(received.sender, "agent_a")

    def test_empty_queue_returns_none(self):
        bus = MessageBus()
        bus.register_agent("agent_x")
        self.assertIsNone(bus.receive("agent_x"))

    def test_message_count(self):
        bus = MessageBus()
        bus.register_agent("a")
        bus.register_agent("b")
        for i in range(5):
            bus.send(Message("a", "b", MessageType.REQUEST, {"i": i}))
        self.assertEqual(bus.message_count(), 5)

    def test_fifo_ordering(self):
        bus = MessageBus()
        bus.register_agent("sender")
        bus.register_agent("receiver")
        for i in range(3):
            bus.send(Message("sender", "receiver", MessageType.REQUEST, {"seq": i}))
        for i in range(3):
            msg = bus.receive("receiver")
            self.assertEqual(msg.payload["seq"], i)


# ── Tool Registry Tests ─────────────────────────────────────────────────────

class TestToolRegistry(unittest.TestCase):
    """Test MCP-style tool registration and discovery."""

    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(ToolDescriptor(
            name="test_tool",
            description="A test tool for unit testing",
            input_schema={"x": "input value"},
            func=lambda x: {"result": x * 2},
            tags=["test", "math"],
        ))

    def test_register_and_list(self):
        tools = self.registry.list_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "test_tool")

    def test_invoke(self):
        result = self.registry.invoke("test_tool", {"x": 21})
        self.assertEqual(result["result"], 42)

    def test_invoke_missing_tool(self):
        result = self.registry.invoke("nonexistent", {})
        self.assertIn("error", result)

    def test_find_by_tag(self):
        matches = self.registry.find_by_tag("math")
        self.assertIn("test_tool", matches)

    def test_find_for_task(self):
        matches = self.registry.find_for_task(["test"])
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0]["name"], "test_tool")


# ── Text Tool Tests ──────────────────────────────────────────────────────────

class TestTextTools(unittest.TestCase):
    """Test text processing MCP tools."""

    def test_extract_questions(self):
        text = (
            "AI is transforming healthcare. What are the benefits? "
            "It reduces errors. How does it improve outcomes? "
            "Costs are a concern."
        )
        result = extract_questions(text)
        self.assertEqual(result["count"], 2)
        self.assertTrue(any("benefits" in q for q in result["questions"]))

    def test_summarize_text(self):
        text = (
            "Artificial intelligence is changing medicine. "
            "Deep learning can detect diseases from images. "
            "This technology improves diagnostic accuracy significantly. "
            "Hospitals are adopting these systems rapidly. "
            "Patient outcomes measurably improve with AI assistance. "
            "Cost reduction is another major benefit observed. "
            "Training data quality remains critically important. "
            "Regulatory frameworks need to evolve accordingly."
        )
        result = summarize_text(text, num_sentences=3)
        self.assertIn("summary", result)
        self.assertIn("method", result)
        self.assertTrue(len(result["summary"]) > 0)

    def test_extract_keywords(self):
        text = (
            "Healthcare artificial intelligence machine learning diagnostics "
            "patient care imaging radiology clinical decision support systems "
            "healthcare healthcare diagnostics diagnostics imaging imaging"
        )
        result = extract_keywords(text, top_n=5)
        self.assertTrue(len(result["keywords"]) <= 5)
        # "healthcare" and "diagnostics" should be top keywords
        self.assertIn("healthcare", result["keywords"][:3])

    def test_analyze_tabular_data(self):
        headers = ["Patient", "Age", "Heart_Rate", "Department"]
        rows = [
            ["P-001", 45, 72, "General"],
            ["P-002", 67, 88, "Cardiology"],
            ["P-003", 55, 76, "General"],
        ]
        result = analyze_tabular_data(headers, rows)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["column_count"], 4)
        self.assertIn("Age", result["column_stats"])
        self.assertEqual(result["column_stats"]["Age"]["type"], "numeric")

    def test_read_text_file_not_found(self):
        result = read_text("/nonexistent/file.txt")
        self.assertIn("error", result)


# ── Execution Plan Tests ─────────────────────────────────────────────────────

class TestExecutionPlan(unittest.TestCase):
    """Test dynamic execution plan behavior."""

    def test_step_ordering_with_dependencies(self):
        plan = ExecutionPlan(task_description="test")
        plan.steps = [
            Step(0, "read_file", "reader", {}),
            Step(1, "analyze", "analyzer", {}, depends_on=[0]),
            Step(2, "summarize", "summarizer", {}, depends_on=[1]),
        ]
        # First executable step should be step 0
        step = plan.next_step()
        self.assertEqual(step.step_id, 0)

        # Step 1 should NOT be next (step 0 not completed)
        step1 = plan.next_step()
        self.assertEqual(step1.step_id, 0)  # still step 0

        # Complete step 0, now step 1 should be available
        plan.steps[0].status = "completed"
        step = plan.next_step()
        self.assertEqual(step.step_id, 1)

    def test_plan_completion(self):
        plan = ExecutionPlan(task_description="test")
        plan.steps = [Step(0, "read", "reader", {})]
        self.assertFalse(plan.is_complete())
        plan.steps[0].status = "completed"
        self.assertTrue(plan.is_complete())


# ── LLM Adapter Tests ───────────────────────────────────────────────────────

class TestLLMAdapter(unittest.TestCase):
    """Test LLM adapter with mock backend."""

    def setUp(self):
        self.adapter = LLMAdapter(backend="mock")

    def test_backend_name(self):
        self.assertEqual(self.adapter.backend_name, "mock")

    def test_enhance_summary(self):
        result = self.adapter.enhance_summary(
            "AI reduced diagnostic errors by 15%.",
            context="Healthcare technology review",
        )
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 20)

    def test_generate_insights(self):
        data = {"Heart_Rate_BPM": {"mean": 80, "max": 96}, "Risk_Level": {"Critical": 3}}
        insights = self.adapter.generate_insights(data)
        self.assertIsInstance(insights, list)
        self.assertTrue(len(insights) >= 1)

    def test_complete_general(self):
        result = self.adapter.complete("Analyze patient data trends")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 10)


# ── Integration Tests ────────────────────────────────────────────────────────

class TestPlannerIntegration(unittest.TestCase):
    """Test the PlannerAgent generates correct plans."""

    def setUp(self):
        self.bus = MessageBus()
        self.registry = build_tool_registry()
        self.planner = PlannerAgent(self.bus, self.registry)

    def test_plan_for_text_summarization(self):
        msg = Message("test", "planner", MessageType.REQUEST, {
            "task": "Summarize this document",
            "files": ["report.txt"],
        })
        result = self.planner.process(msg)
        plan = result["plan"]
        actions = [s.action for s in plan.steps]
        self.assertIn("read_file", actions)
        self.assertIn("summarize", actions)

    def test_plan_for_excel_analysis(self):
        msg = Message("test", "planner", MessageType.REQUEST, {
            "task": "Analyze data and provide insights",
            "files": ["data.xlsx"],
        })
        result = self.planner.process(msg)
        plan = result["plan"]
        actions = [s.action for s in plan.steps]
        self.assertIn("read_file", actions)
        self.assertIn("analyze_data", actions)

    def test_plan_adapts_to_file_type(self):
        msg_txt = Message("test", "planner", MessageType.REQUEST, {
            "task": "Read file", "files": ["doc.txt"],
        })
        msg_pdf = Message("test", "planner", MessageType.REQUEST, {
            "task": "Read file", "files": ["doc.pdf"],
        })
        plan_txt = self.planner.process(msg_txt)["plan"]
        plan_pdf = self.planner.process(msg_pdf)["plan"]

        self.assertEqual(plan_txt.steps[0].params["tool"], "read_text")
        self.assertEqual(plan_pdf.steps[0].params["tool"], "read_pdf")


class TestEndToEnd(unittest.TestCase):
    """Test full system end-to-end with sample data."""

    def test_full_workflow_with_text_file(self):
        sample = os.path.join(
            os.path.dirname(__file__), "..", "sample_data", "sample.txt",
        )
        if not os.path.exists(sample):
            self.skipTest("sample.txt not found")

        from agent_workflow.main import run_task
        # Suppress print output during test
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            results = run_task(
                "Summarize and extract questions",
                [sample],
            )
        self.assertIn("extract_questions", results)
        self.assertIn("summarize", results)
        self.assertTrue(results["extract_questions"]["count"] > 0)


if __name__ == "__main__":
    unittest.main()
