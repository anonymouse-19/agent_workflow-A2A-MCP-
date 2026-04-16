"""
Generate a 10-slide landscape PDF presentation for the Healthcare Multi-Agent
Workflow project (A2A + MCP + Groq).

Usage:
    python generate_slides.py
"""

from reportlab.lib.pagesizes import landscape, LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
import os
import datetime

PAGE_W, PAGE_H = landscape(LETTER)  # 11 x 8.5 inches
OUTPUT_PATH = os.path.join(os.path.dirname(__file__),
                           "Healthcare_Agent_Workflow_Slides.pdf")

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY       = HexColor("#1a237e")
DARK_BLUE  = HexColor("#283593")
MID_BLUE   = HexColor("#3949ab")
LIGHT_BLUE = HexColor("#e8eaf6")
ACCENT     = HexColor("#00897b")
DARK_GRAY  = HexColor("#37474f")
LIGHT_GRAY = HexColor("#eceff1")
CODE_BG    = HexColor("#263238")
WHITE      = white

# ── Styles ───────────────────────────────────────────────────────────────────
_base = getSampleStyleSheet()

styles = {
    "SlideTitle": ParagraphStyle(
        "SlideTitle", parent=_base["Title"],
        fontSize=30, leading=36, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=8,
    ),
    "SlideSubtitle": ParagraphStyle(
        "SlideSubtitle", parent=_base["Normal"],
        fontSize=16, leading=22, textColor=DARK_BLUE, alignment=TA_CENTER,
        spaceAfter=4,
    ),
    "CoverTitle": ParagraphStyle(
        "CoverTitle", parent=_base["Title"],
        fontSize=36, leading=44, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=6,
    ),
    "CoverSub": ParagraphStyle(
        "CoverSub", parent=_base["Normal"],
        fontSize=18, leading=24, textColor=DARK_BLUE, alignment=TA_CENTER,
        spaceAfter=4,
    ),
    "CoverDate": ParagraphStyle(
        "CoverDate", parent=_base["Normal"],
        fontSize=12, leading=16, textColor=DARK_GRAY, alignment=TA_CENTER,
        spaceBefore=14,
    ),
    "Body": ParagraphStyle(
        "Body", parent=_base["Normal"],
        fontSize=13, leading=18, textColor=DARK_GRAY, alignment=TA_LEFT,
        spaceAfter=6, leftIndent=20,
    ),
    "Bullet": ParagraphStyle(
        "Bullet", parent=_base["Normal"],
        fontSize=13, leading=18, textColor=DARK_GRAY,
        leftIndent=40, spaceAfter=5, bulletIndent=24,
    ),
    "SubHead": ParagraphStyle(
        "SubHead", parent=_base["Heading2"],
        fontSize=16, leading=22, textColor=MID_BLUE,
        spaceBefore=10, spaceAfter=4, leftIndent=20,
    ),
    "Code": ParagraphStyle(
        "Code", parent=_base["Normal"],
        fontName="Courier", fontSize=10, leading=13,
        textColor=HexColor("#c5e1a5"), backColor=CODE_BG,
        spaceAfter=8, leftIndent=30, rightIndent=30,
        borderWidth=0.5, borderColor=HexColor("#455a64"), borderPadding=8,
    ),
    "TableHeader": ParagraphStyle(
        "TableHeader", parent=_base["Normal"],
        fontSize=11, leading=14, textColor=WHITE,
        fontName="Helvetica-Bold", alignment=TA_CENTER,
    ),
    "TableCell": ParagraphStyle(
        "TableCell", parent=_base["Normal"],
        fontSize=10, leading=14, textColor=DARK_GRAY, alignment=TA_LEFT,
    ),
    "TableCellCenter": ParagraphStyle(
        "TableCellCenter", parent=_base["Normal"],
        fontSize=10, leading=14, textColor=DARK_GRAY, alignment=TA_CENTER,
    ),
    "Footer": ParagraphStyle(
        "Footer", parent=_base["Normal"],
        fontSize=8, textColor=HexColor("#90a4ae"), alignment=TA_CENTER,
    ),
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def _hr():
    return HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE,
                      spaceAfter=10, spaceBefore=4)

def _bullet(text):
    return Paragraph(f"• {text}", styles["Bullet"])

def _make_table(headers, rows, col_widths=None):
    hdr = [Paragraph(h, styles["TableHeader"]) for h in headers]
    body = []
    for row in rows:
        body.append([
            Paragraph(str(c), styles["TableCell"] if i == 0
                      else styles["TableCellCenter"])
            for i, c in enumerate(row)
        ])
    data = [hdr] + body
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#b0bec5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#90a4ae"))
    canvas.drawCentredString(PAGE_W / 2, 0.35 * inch,
                             f"Healthcare Multi-Agent Workflow — A2A + MCP + Groq  |  Slide {doc.page}")
    canvas.restoreState()


# ── Slide builders ───────────────────────────────────────────────────────────

def slide_1_title(story):
    """Slide 1 — Title slide."""
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("Healthcare Multi-Agent Workflow System",
                           styles["CoverTitle"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="50%", thickness=2, color=ACCENT,
                            spaceAfter=12, spaceBefore=6))
    story.append(Paragraph("A2A Protocol  ·  MCP Tool Integration  ·  Groq LLM",
                           styles["CoverSub"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Production-grade multi-agent system for healthcare data processing",
        styles["CoverSub"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        "Python 3.11 · FastAPI · Redis · Next.js 14 · Docker Compose",
        styles["CoverDate"]))
    story.append(Paragraph(
        f"Presented: {datetime.datetime.now().strftime('%B %d, %Y')}",
        styles["CoverDate"]))
    story.append(PageBreak())


def slide_2_problem(story):
    """Slide 2 — Problem Statement & Motivation."""
    story.append(Paragraph("Problem Statement & Motivation", styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>Challenge</b>", styles["SubHead"]))
    _bullets = [
        "Healthcare data is siloed across PDFs, spreadsheets, and text reports",
        "Manual processing is slow, error-prone, and hard to scale",
        "No standard way for AI agents to discover and communicate with each other",
        "Clinical teams need structured briefs, not raw LLM output",
    ]
    for b in _bullets:
        story.append(_bullet(b))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("<b>Our Solution</b>", styles["SubHead"]))
    _solution = [
        "Multi-agent architecture where specialized agents collaborate autonomously",
        "Adopt <b>Google A2A</b> for agent discovery &amp; communication",
        "Adopt <b>Anthropic MCP</b> for standardized tool access",
        "Use <b>Groq</b> (Llama-3.3-70b) for blazing-fast LLM inference",
        "End-to-end streaming UI with real-time execution trace",
    ]
    for b in _solution:
        story.append(_bullet(b))
    story.append(PageBreak())


def slide_3_architecture(story):
    """Slide 3 — High-Level Architecture."""
    story.append(Paragraph("System Architecture", styles["SlideTitle"]))
    story.append(_hr())

    arch = (
        '<font face="Courier" size="9">'
        "┌──────────────────────────────────────────────────────────────────────┐<br/>"
        "│  <b>Frontend</b> (Next.js 14)                   :3000                    │<br/>"
        "│  Execution Trace (left)  ·  Output / Markdown (right)  · SSE       │<br/>"
        "└─────────────────────────────┬────────────────────────────────────────┘<br/>"
        "                              │ POST /workflow/stream<br/>"
        "┌─────────────────────────────▼────────────────────────────────────────┐<br/>"
        "│  <b>Orchestrator</b> (FastAPI)                  :8000                     │<br/>"
        "│  AgentRegistry · Planner (Groq) · DAG Engine (parallel execution)  │<br/>"
        "└───┬────────────┬────────────┬────────────────────────────────────────┘<br/>"
        "    │ A2A        │ A2A        │ A2A<br/>"
        "┌───▼───┐   ┌───▼────┐   ┌───▼────────┐    ┌─────────────────────────┐<br/>"
        "│Reader │   │Analyzer│   │Summarizer  │    │  <b>MCP Server</b>  :8004     │<br/>"
        "│ :8001 │   │ :8002  │   │  :8003     │    │  FastMCP + 8 tools      │<br/>"
        "└───┬───┘   └───┬────┘   └───┬────────┘    └──────────┬──────────────┘<br/>"
        "    │ MCP        │ MCP        │ MCP                    │<br/>"
        "    └────────────┴────────────┴────────────────────────┘<br/>"
        "                              │<br/>"
        "                        ┌─────▼──────┐<br/>"
        "                        │   Redis    │<br/>"
        "                        │  (shared)  │<br/>"
        "                        └────────────┘"
        "</font>"
    )
    story.append(Paragraph(arch, styles["Body"]))
    story.append(PageBreak())


def slide_4_tech_stack(story):
    """Slide 4 — Technology Stack."""
    story.append(Paragraph("Technology Stack", styles["SlideTitle"]))
    story.append(_hr())

    headers = ["Layer", "Technology", "Why"]
    rows = [
        ["Communication", "Google A2A Protocol",
         "Open standard for agent discovery & inter-agent messaging"],
        ["Tool Integration", "Anthropic MCP (FastMCP)",
         "Standardized tool registry; agents call tools via HTTP"],
        ["LLM Backend", "Groq (Llama-3.3-70b)",
         "~10× faster than OpenAI; free tier; on-prem roadmap"],
        ["API Framework", "FastAPI + Uvicorn",
         "Async-native, auto OpenAPI docs, SSE streaming"],
        ["State / Cache", "Redis 7",
         "Async shared memory between agents; 1-hour TTL"],
        ["Frontend", "Next.js 14 + Tailwind CSS",
         "Server components, SSE streaming, responsive UI"],
        ["Deployment", "Docker Compose",
         "Single-command orchestration of 6 services + Redis"],
        ["Models", "Pydantic v2",
         "Strict data contracts for A2A tasks, plans, traces"],
    ]
    story.append(_make_table(headers, rows,
                             col_widths=[1.4 * inch, 2.2 * inch, 5.4 * inch]))
    story.append(PageBreak())


def slide_5_a2a_protocol(story):
    """Slide 5 — A2A Protocol Deep-Dive."""
    story.append(Paragraph("A2A (Agent-to-Agent) Protocol", styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>What is A2A?</b>", styles["SubHead"]))
    story.append(Paragraph(
        "Google's open standard enabling AI agents to discover each other, "
        "negotiate capabilities, and exchange tasks — regardless of framework.",
        styles["Body"]))

    story.append(Paragraph("<b>How We Use A2A</b>", styles["SubHead"]))
    bullets = [
        "Each agent publishes an <b>Agent Card</b> at <font face='Courier'>/.well-known/agent.json</font> "
        "(name, capabilities, endpoint URL)",
        "Orchestrator <b>discovers</b> agents at startup by fetching Agent Cards",
        "Tasks dispatched via <b>POST /tasks/send</b> with <font face='Courier'>{id, correlation_id, input}</font>",
        "Real-time streaming via <b>POST /tasks/stream</b> using Server-Sent Events",
        "Response includes status transitions: <b>submitted → working → completed</b>",
    ]
    for b in bullets:
        story.append(_bullet(b))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Agent Card (example)</b>", styles["SubHead"]))
    code = (
        '{ "name": "reader-agent",<br/>'
        '  "description": "Reads PDF, Excel, text files via MCP tools",<br/>'
        '  "url": "http://reader:8001",<br/>'
        '  "capabilities": ["read_pdf","read_excel","read_text"] }'
    )
    story.append(Paragraph(code, styles["Code"]))
    story.append(PageBreak())


def slide_6_mcp_protocol(story):
    """Slide 6 — MCP Protocol & Tool Registry."""
    story.append(Paragraph("MCP (Model Context Protocol) & Tools",
                           styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>What is MCP?</b>", styles["SubHead"]))
    story.append(Paragraph(
        "Anthropic's open standard for connecting LLMs to external tools and "
        "data sources via a unified HTTP interface.",
        styles["Body"]))

    story.append(Paragraph("<b>8 Registered Tools</b>", styles["SubHead"]))
    headers = ["Tool", "Category", "Description"]
    rows = [
        ["read_pdf",            "File I/O",  "Extract text from PDF documents"],
        ["read_excel",          "File I/O",  "Parse Excel workbooks to structured data"],
        ["read_text",           "File I/O",  "Read plain text / CSV / Markdown files"],
        ["extract_questions",   "NLP",       "Identify clinical questions in text"],
        ["extract_keywords",    "NLP",       "TF-based keyword extraction"],
        ["summarize_text",      "NLP",       "Extractive text summarization"],
        ["analyze_tabular_data","Analytics", "Stats, anomalies, trend detection"],
        ["llm_enhance",         "LLM",       "Groq-powered clinical interpretation"],
    ]
    story.append(_make_table(headers, rows,
                             col_widths=[1.8 * inch, 1.2 * inch, 5.4 * inch]))
    story.append(PageBreak())


def slide_7_agents(story):
    """Slide 7 — Agent Microservices."""
    story.append(Paragraph("Agent Microservices", styles["SlideTitle"]))
    story.append(_hr())

    agents = [
        ("Orchestrator  — Port 8000", [
            "Discovers agents &amp; MCP tools at startup",
            "Sends goal to Groq planner → receives an <b>Execution Plan</b> (DAG of steps)",
            "Executes steps in parallel respecting dependencies",
            "Streams trace events (SSE) to frontend in real time",
            "Supports human-in-the-loop approval for sensitive steps",
        ]),
        ("Reader Agent  — Port 8001", [
            "Reads files (PDF, Excel, text, CSV, Markdown) via MCP tools",
            "Dynamically selects the right tool based on file extension",
        ]),
        ("Analyzer Agent  — Port 8002", [
            "Extracts questions, keywords; runs tabular analysis",
            "Optionally enhances analysis with Groq LLM interpretation",
        ]),
        ("Summarizer Agent  — Port 8003", [
            "Creates extractive summaries; compiles clinical briefs",
            "Combines text + analysis → structured AI-enriched documents",
        ]),
    ]
    for title, bullets in agents:
        story.append(Paragraph(f"<b>{title}</b>", styles["SubHead"]))
        for b in bullets:
            story.append(_bullet(b))
    story.append(PageBreak())


def slide_8_workflow(story):
    """Slide 8 — End-to-End Workflow & Data Flow."""
    story.append(Paragraph("Workflow & Data Flow", styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>End-to-End Execution</b>", styles["SubHead"]))
    steps = [
        "<b>1.</b> User submits a goal + files via the Next.js UI",
        "<b>2.</b> Orchestrator sends goal to <b>Groq Planner</b> → returns ExecutionPlan (DAG)",
        "<b>3.</b> DAG engine resolves dependencies and runs steps in <b>parallel</b>",
        "<b>4.</b> Each step dispatches an A2A task to the appropriate agent",
        "<b>5.</b> Agents call MCP tools, optionally enhance with Groq, return results",
        "<b>6.</b> Results stored in <b>Redis</b> (keyed by correlation_id + step_id)",
        "<b>7.</b> Downstream steps receive upstream results as context automatically",
        "<b>8.</b> Trace events streamed to UI in real time via SSE",
    ]
    for s in steps:
        story.append(Paragraph(s, styles["Bullet"]))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("<b>Key Design Decisions</b>", styles["SubHead"]))
    decisions = [
        "<b>DAG execution</b> — steps with no dependencies run concurrently",
        "<b>Redis context passing</b> — agents share state without direct coupling",
        "<b>Token tracking</b> — every Groq call logged; aggregated in orchestrator &amp; UI",
        "<b>Human-in-the-loop</b> — optional approval gates for sensitive clinical workflows",
    ]
    for d in decisions:
        story.append(_bullet(d))
    story.append(PageBreak())


def slide_9_frontend(story):
    """Slide 9 — Frontend & Demo."""
    story.append(Paragraph("Frontend & Live Demo", styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>Next.js 14 Streaming UI (Port 3000)</b>",
                           styles["SubHead"]))
    features = [
        "<b>Left panel:</b> Real-time execution trace — shows each agent/tool step as it runs",
        "<b>Right panel:</b> Tabbed results — clinical brief, extractive summary, keywords, questions",
        "Markdown rendering for structured clinical documents",
        "Token usage &amp; estimated cost display per step and total",
        "File upload with automatic type detection",
        "Responsive layout with Tailwind CSS",
    ]
    for f in features:
        story.append(_bullet(f))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("<b>Quick-Start Commands</b>", styles["SubHead"]))
    code = (
        "# Docker (recommended)<br/>"
        "cp .env.example .env   # add GROQ_API_KEY<br/>"
        "docker-compose up --build<br/>"
        "# Open http://localhost:3000"
    )
    story.append(Paragraph(code, styles["Code"]))
    story.append(PageBreak())


def slide_10_summary(story):
    """Slide 10 — Summary & Next Steps."""
    story.append(Paragraph("Summary & Next Steps", styles["SlideTitle"]))
    story.append(_hr())

    story.append(Paragraph("<b>What We Built</b>", styles["SubHead"]))
    summary = [
        "Production-grade <b>multi-agent system</b> for healthcare data processing",
        "Implements <b>Google A2A</b> (agent communication) + <b>Anthropic MCP</b> (tool access)",
        "Powered by <b>Groq</b> (Llama-3.3-70b) — ~10× faster than cloud LLMs",
        "<b>6 microservices</b> orchestrated via Docker Compose with Redis shared state",
        "Real-time <b>streaming UI</b> with execution trace &amp; structured clinical output",
    ]
    for s in summary:
        story.append(_bullet(s))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("<b>Next Steps</b>", styles["SubHead"]))
    nexts = [
        "Add authentication &amp; RBAC for production deployment",
        "Integrate FHIR-compliant healthcare data standards",
        "Support additional LLM backends (OpenAI, Anthropic) as fallbacks",
        "Add agent auto-scaling with Kubernetes",
        "Expand MCP tool registry (HL7 parser, DICOM reader, lab-result analyzer)",
    ]
    for n in nexts:
        story.append(_bullet(n))

    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="40%", thickness=2, color=ACCENT,
                            spaceAfter=12, spaceBefore=6))
    story.append(Paragraph("Thank You", styles["CoverTitle"]))
    story.append(Paragraph(
        "Built with Python 3.11 · FastAPI · Groq · Redis · Next.js 14 · Docker",
        styles["CoverDate"]))


# ── Main ─────────────────────────────────────────────────────────────────────

def build():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=landscape(LETTER),
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )

    story = []

    # Build all 10 slides
    slide_1_title(story)
    slide_2_problem(story)
    slide_3_architecture(story)
    slide_4_tech_stack(story)
    slide_5_a2a_protocol(story)
    slide_6_mcp_protocol(story)
    slide_7_agents(story)
    slide_8_workflow(story)
    slide_9_frontend(story)
    slide_10_summary(story)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"\n✅ Slide deck generated: {OUTPUT_PATH}")
    print(f"   Slides: {doc.page}")
    print(f"   Size:   {os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
