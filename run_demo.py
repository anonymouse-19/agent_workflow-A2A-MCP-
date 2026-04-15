#!/usr/bin/env python3
"""
Demo Runner — Showcases the Agent Workflow System with multiple scenarios.

Demonstrates:
  - A2A message-based communication between agents
  - MCP-style dynamic tool discovery and invocation
  - Non-hardcoded, runtime-generated execution plans
  - Adaptive behavior based on input type and task
  - LLM-ready architecture with pluggable AI backend

Run from the project root:
  python run_demo.py
"""

import os
import sys
import time

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_workflow.main import run_task, setup, build_tool_registry


# ── ANSI Colors for terminal output ──────────────────────────────────────────

class _C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"


def _color_supported():
    """Check if the terminal likely supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        # Windows 10+ supports ANSI in modern terminals
        os.system("")  # enables ANSI escape processing
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


if not _color_supported():
    # Disable colors if not supported
    for attr in dir(_C):
        if not attr.startswith("_"):
            setattr(_C, attr, "")


def _ensure_samples():
    """Auto-generate sample data files if they don't exist."""
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    xlsx_path = os.path.join(sample_dir, "patient_data.xlsx")
    pdf_path = os.path.join(sample_dir, "report.pdf")

    if not os.path.exists(xlsx_path) or not os.path.exists(pdf_path):
        print(f"\n  {_C.YELLOW}Generating sample data files...{_C.RESET}")
        sys.path.insert(0, sample_dir)
        from sample_data.create_samples import create_excel_sample, create_pdf_sample
        if not os.path.exists(xlsx_path):
            create_excel_sample()
        if not os.path.exists(pdf_path):
            create_pdf_sample()
        print()


def demo_separator(title: str):
    print(f"\n\n{_C.BOLD}{_C.CYAN}{'#' * 78}")
    print(f"#  DEMO: {title}")
    print(f"{'#' * 78}{_C.RESET}")


def demo_1_summarize_and_extract():
    """Demo 1: Summarize a clinical text and extract questions."""
    demo_separator("Summarize Clinical Document & Extract Questions")
    sample = os.path.join("sample_data", "sample.txt")

    if not os.path.exists(sample):
        print(f"  {_C.RED}[!] Sample file not found: {sample}{_C.RESET}")
        return

    run_task(
        task="Summarize this document and extract all questions",
        files=[sample],
    )


def demo_2_analyze_patient_data():
    """Demo 2: Analyze patient vitals and device utilization."""
    demo_separator("Analyze Patient Data & Device Utilization")
    sample = os.path.join("sample_data", "patient_data.xlsx")

    if not os.path.exists(sample):
        print(f"  {_C.RED}[!] Patient data not found: {sample}{_C.RESET}")
        return

    run_task(
        task="Analyze data and provide insights and statistics",
        files=[sample],
    )


def demo_3_multi_file():
    """Demo 3: Process multiple healthcare files in one task."""
    demo_separator("Multi-File Processing (Clinical Text + Patient Data)")
    txt_file = os.path.join("sample_data", "sample.txt")
    xlsx_file = os.path.join("sample_data", "patient_data.xlsx")

    files = [f for f in [txt_file, xlsx_file] if os.path.exists(f)]
    if not files:
        print(f"  {_C.RED}[!] No sample files found. Skipping.{_C.RESET}")
        return

    run_task(
        task="Summarize all documents and analyze data trends",
        files=files,
    )


def demo_4_keyword_extraction():
    """Demo 4: Extract keywords from a clinical document."""
    demo_separator("Clinical Keyword Extraction")
    sample = os.path.join("sample_data", "sample.txt")

    if not os.path.exists(sample):
        print(f"  {_C.RED}[!] Sample file not found: {sample}{_C.RESET}")
        return

    run_task(
        task="Extract the most important keywords and topics",
        files=[sample],
    )


def demo_5_tool_registry():
    """Demo 5: Show the MCP tool registry (tool discovery)."""
    demo_separator("MCP Tool Registry — Available Tools")
    registry = build_tool_registry()
    tools = registry.list_tools()

    print(f"\n  {_C.BOLD}Registered Tools ({len(tools)}):{_C.RESET}")
    print(f"  {'─' * 60}")
    for tool in tools:
        print(f"    {_C.GREEN}[{tool['name']}]{_C.RESET}")
        print(f"      Description: {tool['description']}")
        print(f"      Tags:        {', '.join(tool['tags'])}")
        print(f"      Params:      {tool['input_schema']}")
        print()

    # Show dynamic search
    print(f"  {_C.BOLD}Dynamic Tool Search Examples:{_C.RESET}")
    print(f"  {'─' * 60}")
    for query in ["pdf", "analysis", "summary"]:
        matches = registry.find_for_task([query])
        names = [m["name"] for m in matches]
        print(f"    Query '{_C.CYAN}{query}{_C.RESET}' → {names}")


def demo_6_system_architecture():
    """Demo 6: Display the system architecture."""
    demo_separator("System Architecture Overview")

    print(f"""
  {_C.BOLD}┌─────────────────────────────────────────────────────────────────┐
  │              PHILIPS AGENT WORKFLOW SYSTEM                     │
  │      A2A Communication  +  MCP Tools  +  LLM-Ready            │
  ├─────────────────────────────────────────────────────────────────┤{_C.RESET}
  │                                                                 │
  │   {_C.CYAN}┌───────────┐{_C.RESET}      A2A Messages       {_C.MAGENTA}┌───────────────┐{_C.RESET}      │
  │   {_C.CYAN}│   USER    │{_C.RESET} ──────────────────────►  {_C.MAGENTA}│  ORCHESTRATOR │{_C.RESET}      │
  │   {_C.CYAN}└───────────┘{_C.RESET}                          {_C.MAGENTA}└───────┬───────┘{_C.RESET}      │
  │                                                  │              │
  │                              {_C.YELLOW}┌───────────────────┼──────┐{_C.RESET}       │
  │                              {_C.YELLOW}│    MESSAGE BUS    │      │{_C.RESET}       │
  │                              {_C.YELLOW}│    (A2A Router)   │      │{_C.RESET}       │
  │                              {_C.YELLOW}└───┬───────┬───────┘──────┘{_C.RESET}       │
  │                                  │       │       │              │
  │                     ┌────────────┤       │       ├──────────┐   │
  │                     ▼            ▼       ▼       ▼          │   │
  │              {_C.GREEN}┌──────────┐ ┌────────┐ ┌────────┐ ┌─────────┐{_C.RESET}│   │
  │              {_C.GREEN}│ PLANNER  │ │ READER │ │ANALYZER│ │SUMMARIZE│{_C.RESET}│   │
  │              {_C.GREEN}│  Agent   │ │ Agent  │ │ Agent  │ │  Agent  │{_C.RESET}│   │
  │              {_C.GREEN}└──────────┘ └───┬────┘ └───┬────┘ └────┬────┘{_C.RESET}│   │
  │                               │          │           │      │   │
  │                  {_C.DIM}┌────────────┴──────────┴───────────┴──┐{_C.RESET}   │   │
  │                  {_C.DIM}│       MCP TOOL REGISTRY              │{_C.RESET}   │   │
  │                  {_C.DIM}│  read_pdf  │ read_excel │ read_text  │{_C.RESET}   │   │
  │                  {_C.DIM}│  extract_q │ summarize  │ keywords   │{_C.RESET}   │   │
  │                  {_C.DIM}│  analyze   │ llm_enhance│            │{_C.RESET}   │   │
  │                  {_C.DIM}└────────────────────────────────────  ┘{_C.RESET}   │   │
  │                                                                 │
  │   {_C.BOLD}┌─ LLM ADAPTER ───────────────────────────────────────┐{_C.RESET}      │
  │   {_C.BOLD}│  OpenAI / Ollama / Mock — pluggable AI backend      │{_C.RESET}      │
  │   {_C.BOLD}└──────────────────────────────────────────────────────┘{_C.RESET}      │
  └─────────────────────────────────────────────────────────────────┘

  {_C.BOLD}KEY DESIGN PRINCIPLES:{_C.RESET}
    {_C.GREEN}•{_C.RESET} A2A: Agents communicate only via Message objects through the MessageBus.
    {_C.GREEN}•{_C.RESET} MCP: Tools are registered centrally; agents discover and invoke dynamically.
    {_C.GREEN}•{_C.RESET} Non-Hardcoded: PlannerAgent generates execution plans at runtime.
    {_C.GREEN}•{_C.RESET} Adaptive: Failed steps are skipped; remaining steps continue executing.
    {_C.GREEN}•{_C.RESET} LLM-Ready: Pluggable AI backend (OpenAI, Ollama, or offline mock).
    {_C.GREEN}•{_C.RESET} Healthcare: Designed for clinical data, patient vitals, and medical imaging.
""")


def demo_7_llm_enhancement():
    """Demo 7: Show LLM-enhanced analysis (mock mode)."""
    demo_separator("LLM-Enhanced Clinical Analysis (Mock Mode)")

    from agent_workflow.llm_adapter import LLMAdapter

    adapter = LLMAdapter()  # defaults to mock
    print(f"\n  {_C.BOLD}LLM Backend:{_C.RESET} {adapter.backend_name}")
    print(f"  {'─' * 60}")

    # Demo: clinical text enhancement
    sample_summary = (
        "AI-assisted imaging reduced diagnostic errors by 15%. "
        "Telemedicine adoption increased 23%. Remote monitoring improved outcomes."
    )
    print(f"\n  {_C.BOLD}Input Summary:{_C.RESET}")
    print(f"    {sample_summary}")

    enhanced = adapter.enhance_summary(
        summary=sample_summary,
        context="Healthcare AI clinical review document",
    )
    print(f"\n  {_C.BOLD}LLM-Enhanced Output:{_C.RESET}")
    print(f"    {enhanced}")

    # Demo: clinical insight generation
    sample_data = {
        "Heart_Rate_BPM": {"mean": 81.2, "min": 68, "max": 96},
        "SpO2_Percent": {"mean": 95.8, "min": 91, "max": 99},
        "Risk_Level": {"Critical": 3, "High": 2, "Medium": 3, "Low": 4},
    }
    print(f"\n  {_C.BOLD}Patient Data Statistics:{_C.RESET}")
    for k, v in sample_data.items():
        print(f"    {k}: {v}")

    insights = adapter.generate_insights(sample_data)
    print(f"\n  {_C.BOLD}LLM-Generated Clinical Insights:{_C.RESET}")
    for i, insight in enumerate(insights, 1):
        print(f"    {i}. {insight}")


if __name__ == "__main__":
    print(f"\n{_C.BOLD}{'═' * 78}")
    print(f"  PHILIPS AGENT WORKFLOW SYSTEM — DEMONSTRATION")
    print(f"  A2A Communication + MCP Tool Integration + Dynamic Planning + LLM")
    print(f"{'═' * 78}{_C.RESET}")

    # Auto-generate sample data if missing
    _ensure_samples()

    # Show architecture first
    demo_6_system_architecture()

    # Show tool registry
    demo_5_tool_registry()

    # Show LLM capabilities
    demo_7_llm_enhancement()

    # Run functional demos
    demo_1_summarize_and_extract()
    demo_4_keyword_extraction()
    demo_2_analyze_patient_data()

    print(f"\n{_C.BOLD}{_C.GREEN}{'═' * 78}")
    print(f"  ALL DEMOS COMPLETED SUCCESSFULLY")
    print(f"{'═' * 78}{_C.RESET}\n")
