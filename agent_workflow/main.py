"""
Main entry point for the Agent Workflow System.

Sets up the MessageBus, ToolRegistry, Agents, and Orchestrator,
then runs the requested task.

Usage:
  python -m agent_workflow.main "Summarize and extract questions" sample_data/sample.txt
  python -m agent_workflow.main "Analyze data and provide insights" sample_data/sales.xlsx
"""

import sys
import os

from .core.message_bus import MessageBus
from .core.models import ExecutionTrace
from .tools.registry import ToolRegistry, ToolDescriptor
from .tools.pdf_tool import read_pdf
from .tools.excel_tool import read_excel
from .tools.text_tool import (
    read_text, extract_questions, summarize_text,
    extract_keywords, analyze_tabular_data,
)
from .llm_adapter import LLMAdapter
from .agents.planner import PlannerAgent
from .agents.reader import ReaderAgent
from .agents.analyzer import AnalyzerAgent
from .agents.summarizer import SummarizerAgent
from .orchestrator import Orchestrator


def build_tool_registry() -> ToolRegistry:
    """Register all MCP tools in the central registry."""
    registry = ToolRegistry()
    llm = LLMAdapter()

    registry.register(ToolDescriptor(
        name="read_pdf",
        description="Read and extract text from PDF files",
        input_schema={"file_path": "Absolute or relative path to the PDF file"},
        func=read_pdf,
        tags=["file", "pdf", "read"],
    ))
    registry.register(ToolDescriptor(
        name="read_excel",
        description="Read data from Excel spreadsheets (.xlsx)",
        input_schema={"file_path": "Absolute or relative path to the Excel file"},
        func=read_excel,
        tags=["file", "excel", "read"],
    ))
    registry.register(ToolDescriptor(
        name="read_text",
        description="Read content from plain text or CSV files",
        input_schema={"file_path": "Absolute or relative path to the text file"},
        func=read_text,
        tags=["file", "text", "read"],
    ))
    registry.register(ToolDescriptor(
        name="extract_questions",
        description="Extract all questions from text content",
        input_schema={"text": "The text to scan for questions"},
        func=extract_questions,
        tags=["analysis", "questions", "text"],
    ))
    registry.register(ToolDescriptor(
        name="summarize_text",
        description="Create an extractive summary of text using TF scoring",
        input_schema={"text": "The text to summarize", "num_sentences": "(optional) Number of sentences"},
        func=summarize_text,
        tags=["summary", "text"],
    ))
    registry.register(ToolDescriptor(
        name="extract_keywords",
        description="Extract the most important keywords from text",
        input_schema={"text": "The text to analyze", "top_n": "(optional) Number of keywords"},
        func=extract_keywords,
        tags=["analysis", "keywords", "text"],
    ))
    registry.register(ToolDescriptor(
        name="analyze_tabular_data",
        description="Analyze tabular/spreadsheet data with statistics and insights",
        input_schema={"headers": "List of column headers", "rows": "List of data rows"},
        func=analyze_tabular_data,
        tags=["analysis", "data", "statistics"],
    ))
    registry.register(ToolDescriptor(
        name="llm_enhance",
        description="Enhance text analysis using LLM (or mock fallback)",
        input_schema={"text": "Text to enhance", "context": "(optional) Additional context"},
        func=lambda text, context="": llm.enhance_summary(text, context),
        tags=["llm", "enhance", "ai", "summary"],
    ))

    return registry


def setup():
    """Wire up the entire system: bus, tools, agents, orchestrator."""
    bus = MessageBus()
    trace = ExecutionTrace()
    registry = build_tool_registry()

    agents = {
        "planner": PlannerAgent(bus, registry),
        "reader": ReaderAgent(bus, registry),
        "analyzer": AnalyzerAgent(bus, registry),
        "summarizer": SummarizerAgent(bus, registry),
    }

    orchestrator = Orchestrator(bus, agents, trace)
    return orchestrator, trace, bus


def run_task(task: str, files: list) -> dict:
    """Run a task through the agent workflow system."""
    orchestrator, trace, bus = setup()

    print(f"\n{'═' * 78}")
    print(f"  AGENT WORKFLOW SYSTEM")
    print(f"{'═' * 78}")
    print(f"  Task:  {task}")
    print(f"  Files: {', '.join(files)}")
    print(f"{'═' * 78}")
    print(f"\n  Live Execution Log:")
    print(f"  {'─' * 70}")

    results = orchestrator.execute(task, files)

    # Display execution trace
    trace.display()

    # Display final results
    print(f"\n{'═' * 78}")
    print(f"  FINAL RESULTS")
    print(f"{'═' * 78}")

    for action, result in results.items():
        print(f"\n  ┌─ {action.upper()} {'─' * (60 - len(action))}")
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, str) and len(v) > 200:
                    print(f"  │  {k}: {v[:200]}...")
                elif isinstance(v, list) and len(v) > 10:
                    print(f"  │  {k}: [{', '.join(str(x) for x in v[:10])} ...]")
                elif isinstance(v, dict) and len(str(v)) > 200:
                    print(f"  │  {k}:")
                    for dk, dv in v.items():
                        print(f"  │    {dk}: {str(dv)[:100]}")
                else:
                    print(f"  │  {k}: {v}")
        else:
            print(f"  │  {result}")
        print(f"  └{'─' * 65}")

    # Message bus stats
    print(f"\n  A2A Stats: {bus.message_count()} messages exchanged")
    print(f"{'═' * 78}\n")

    return results


def main():
    if len(sys.argv) < 3:
        print("Agent Workflow System — A2A + MCP Dynamic Agent Pipeline")
        print()
        print("Usage:")
        print('  python -m agent_workflow.main "<task>" <file1> [file2] ...')
        print()
        print("Examples:")
        print('  python -m agent_workflow.main "Summarize and extract questions" sample_data/sample.txt')
        print('  python -m agent_workflow.main "Analyze data and provide insights" sample_data/sales.xlsx')
        print('  python -m agent_workflow.main "Summarize this document" sample_data/report.pdf')
        sys.exit(1)

    task = sys.argv[1]
    files = sys.argv[2:]
    run_task(task, files)


if __name__ == "__main__":
    main()
