"""
Planner Agent — Dynamically generates execution plans at runtime.

This is the brain of the system. Given a task description and a list of files,
the Planner:
  1. Analyzes the task to understand what's needed
  2. Inspects file types to determine which tools/agents to involve
  3. Builds a dependency graph of Steps
  4. Returns an ExecutionPlan — NO hardcoded pipelines

The plan adapts based on:
  - Input file types (PDF, Excel, text)
  - Requested operations (summarize, analyze, extract questions)
  - Available tools in the registry
"""

import os
from .base import BaseAgent
from ..core.models import Step, ExecutionPlan


class PlannerAgent(BaseAgent):

    def __init__(self, bus, tools):
        super().__init__(
            name="planner",
            capabilities=["planning", "task_analysis", "routing"],
            bus=bus,
            tools=tools,
        )

    def process(self, message):
        task = message.payload.get("task", "")
        files = message.payload.get("files", [])
        plan = self._create_plan(task, files)
        return {"plan": plan}

    def _create_plan(self, task: str, files: list) -> ExecutionPlan:
        """Dynamically generate an execution plan based on task + files."""
        plan = ExecutionPlan(task_description=task)
        task_lower = task.lower()
        step_id = 0
        read_step_ids = []

        # ── Phase 1: File Reading ────────────────────────────────────────
        # Determine which reader tool to use based on file extension.
        # The agent consults the tool registry to find matches.
        tool_map = {
            ".pdf": "read_pdf",
            ".xlsx": "read_excel",
            ".xls": "read_excel",
            ".txt": "read_text",
            ".csv": "read_text",
            ".md": "read_text",
        }

        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            tool_name = tool_map.get(ext)

            if not tool_name:
                # MCP-style discovery: ask registry for a reader tool
                candidates = self.tools.find_for_task(["read", ext.replace(".", "")])
                tool_name = candidates[0]["name"] if candidates else "read_text"

            plan.steps.append(Step(
                step_id=step_id,
                action="read_file",
                agent="reader",
                params={"tool": tool_name, "file_path": file_path},
            ))
            read_step_ids.append(step_id)
            step_id += 1

        # ── Phase 2: Processing (determined by task keywords) ────────────
        processing_ids = []

        if _matches(task_lower, ["question", "extract question", "quiz", "q&a"]):
            plan.steps.append(Step(
                step_id=step_id,
                action="extract_questions",
                agent="analyzer",
                params={"operation": "extract_questions"},
                depends_on=list(read_step_ids),
            ))
            processing_ids.append(step_id)
            step_id += 1

        if _matches(task_lower, ["analy", "insight", "statistic", "trend", "data"]):
            plan.steps.append(Step(
                step_id=step_id,
                action="analyze_data",
                agent="analyzer",
                params={"operation": "analyze_data"},
                depends_on=list(read_step_ids),
            ))
            processing_ids.append(step_id)
            step_id += 1

        if _matches(task_lower, ["keyword", "key word", "important word", "topic"]):
            plan.steps.append(Step(
                step_id=step_id,
                action="extract_keywords",
                agent="analyzer",
                params={"operation": "extract_keywords"},
                depends_on=list(read_step_ids),
            ))
            processing_ids.append(step_id)
            step_id += 1

        # ── Phase 3: Summarization ───────────────────────────────────────
        if _matches(task_lower, ["summar", "overview", "brief", "digest", "recap"]):
            plan.steps.append(Step(
                step_id=step_id,
                action="summarize",
                agent="summarizer",
                params={},
                depends_on=processing_ids if processing_ids else list(read_step_ids),
            ))
            step_id += 1

        # ── Fallback: if no specific ops requested, do keywords + summary ─
        if not processing_ids and read_step_ids:
            has_summary = any(s.action == "summarize" for s in plan.steps)
            if not has_summary:
                plan.steps.append(Step(
                    step_id=step_id,
                    action="extract_keywords",
                    agent="analyzer",
                    params={"operation": "extract_keywords"},
                    depends_on=list(read_step_ids),
                ))
                kw_id = step_id
                step_id += 1
                plan.steps.append(Step(
                    step_id=step_id,
                    action="summarize",
                    agent="summarizer",
                    params={},
                    depends_on=list(read_step_ids),
                ))
                step_id += 1

        return plan


def _matches(text: str, keywords: list) -> bool:
    """Check if any keyword fragment appears in the text."""
    return any(kw in text for kw in keywords)
