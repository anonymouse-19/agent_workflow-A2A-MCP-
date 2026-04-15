"""
Generate a comprehensive PDF document for the Healthcare Multi-Agent Workflow project.
Covers: setup instructions, architecture, API reference, technology choices, and presentation notes.
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem, KeepTogether,
    Image as RLImage,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderPDF
import os, datetime

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "sample_data",
                           "Healthcare_MultiAgent_System_Documentation.pdf")

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY       = HexColor("#1a237e")
DARK_BLUE  = HexColor("#283593")
MID_BLUE   = HexColor("#3949ab")
LIGHT_BLUE = HexColor("#e8eaf6")
ACCENT     = HexColor("#00897b")
DARK_GRAY  = HexColor("#37474f")
LIGHT_GRAY = HexColor("#eceff1")
CODE_BG    = HexColor("#263238")
WHITE      = white

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

styles.add(ParagraphStyle("CoverTitle", parent=styles["Title"],
    fontSize=32, leading=40, textColor=NAVY, alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle("CoverSubtitle", parent=styles["Normal"],
    fontSize=16, leading=22, textColor=DARK_BLUE, alignment=TA_CENTER, spaceAfter=6))
styles.add(ParagraphStyle("CoverDate", parent=styles["Normal"],
    fontSize=12, leading=16, textColor=DARK_GRAY, alignment=TA_CENTER, spaceBefore=20))
styles.add(ParagraphStyle("SectionTitle", parent=styles["Heading1"],
    fontSize=22, leading=28, textColor=NAVY, spaceBefore=24, spaceAfter=10,
    borderWidth=0, borderColor=NAVY, borderPadding=0))
styles.add(ParagraphStyle("SubSection", parent=styles["Heading2"],
    fontSize=16, leading=22, textColor=DARK_BLUE, spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle("SubSubSection", parent=styles["Heading3"],
    fontSize=13, leading=18, textColor=MID_BLUE, spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=DARK_GRAY, alignment=TA_JUSTIFY,
    spaceAfter=8, leftIndent=0))
styles.add(ParagraphStyle("BodyIndent", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=DARK_GRAY, alignment=TA_JUSTIFY,
    spaceAfter=6, leftIndent=18))
styles.add(ParagraphStyle("CodeBlock", parent=styles["Normal"],
    fontName="Courier", fontSize=9, leading=12, textColor=HexColor("#c5e1a5"),
    backColor=CODE_BG, spaceAfter=8, leftIndent=12, rightIndent=12,
    borderWidth=0.5, borderColor=HexColor("#455a64"), borderPadding=8))
styles.add(ParagraphStyle("CodeInline", parent=styles["Normal"],
    fontName="Courier", fontSize=9.5, textColor=HexColor("#1565c0")))
styles.add(ParagraphStyle("BulletBody", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=DARK_GRAY, leftIndent=24,
    spaceAfter=4, bulletIndent=12))
styles.add(ParagraphStyle("TableHeader", parent=styles["Normal"],
    fontSize=10, leading=13, textColor=WHITE, fontName="Helvetica-Bold",
    alignment=TA_CENTER))
styles.add(ParagraphStyle("TableCell", parent=styles["Normal"],
    fontSize=9.5, leading=13, textColor=DARK_GRAY, alignment=TA_LEFT))
styles.add(ParagraphStyle("TableCellCenter", parent=styles["Normal"],
    fontSize=9.5, leading=13, textColor=DARK_GRAY, alignment=TA_CENTER))
styles.add(ParagraphStyle("FooterStyle", parent=styles["Normal"],
    fontSize=8, textColor=HexColor("#90a4ae"), alignment=TA_CENTER))
styles.add(ParagraphStyle("TOCEntry", parent=styles["Normal"],
    fontSize=12, leading=18, textColor=DARK_BLUE, spaceBefore=4, spaceAfter=2,
    leftIndent=20))
styles.add(ParagraphStyle("TOCSub", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=DARK_GRAY, spaceBefore=2, spaceAfter=1,
    leftIndent=40))
styles.add(ParagraphStyle("Callout", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=HexColor("#004d40"),
    backColor=HexColor("#e0f2f1"), borderWidth=0.5, borderColor=ACCENT,
    borderPadding=10, spaceAfter=12, leftIndent=8, rightIndent=8))
styles.add(ParagraphStyle("Warning", parent=styles["Normal"],
    fontSize=10.5, leading=15, textColor=HexColor("#bf360c"),
    backColor=HexColor("#fbe9e7"), borderWidth=0.5, borderColor=HexColor("#e64a19"),
    borderPadding=10, spaceAfter=12, leftIndent=8, rightIndent=8))

# ── Helpers ───────────────────────────────────────────────────────────────────
def hr():
    return HRFlowable(width="100%", thickness=1, color=LIGHT_BLUE, spaceAfter=12, spaceBefore=6)

def bullet(text, style="BulletBody"):
    return Paragraph(f"• {text}", styles[style])

def numbered(items):
    els = []
    for i, txt in enumerate(items, 1):
        els.append(Paragraph(f"<b>{i}.</b> {txt}", styles["BulletBody"]))
    return els

def code_block(text):
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(escaped, styles["CodeBlock"])

def make_table(headers, rows, col_widths=None):
    hdr = [Paragraph(h, styles["TableHeader"]) for h in headers]
    data = [hdr]
    for row in rows:
        data.append([Paragraph(str(c), styles["TableCell"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME",  (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, 0), 10),
        ("ALIGN",     (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND",(0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("GRID",      (0, 0), (-1, -1), 0.5, HexColor("#b0bec5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#90a4ae"))
    canvas.drawCentredString(LETTER[0] / 2, 30,
        f"Healthcare Multi-Agent Workflow System  |  Page {doc.page}")
    canvas.restoreState()

# ── Build Document ────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=LETTER,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
        leftMargin=0.85*inch, rightMargin=0.85*inch)
    story = []

    # ╔════════════════════════════════════════════════════════════════════════╗
    # ║ COVER PAGE                                                           ║
    # ╚════════════════════════════════════════════════════════════════════════╝
    story.append(Spacer(1, 1.8*inch))
    story.append(Paragraph("Healthcare Multi-Agent<br/>Workflow System", styles["CoverTitle"]))
    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(width="60%", thickness=3, color=ACCENT, spaceAfter=18, spaceBefore=6))
    story.append(Paragraph("A2A + MCP + Groq — Production-Grade Architecture", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("Setup Guide  •  Architecture Deep-Dive  •  API Reference  •  Interview Presentation", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.8*inch))
    story.append(Paragraph("Philips Healthcare — Intelligent Agent Platform", styles["CoverSubtitle"]))
    story.append(Paragraph(f"Prepared: {datetime.date.today().strftime('%B %d, %Y')}", styles["CoverDate"]))
    story.append(Paragraph("Classification: Internal — Interview Documentation", styles["CoverDate"]))
    story.append(PageBreak())

    # ╔════════════════════════════════════════════════════════════════════════╗
    # ║ TABLE OF CONTENTS                                                    ║
    # ╚════════════════════════════════════════════════════════════════════════╝
    story.append(Paragraph("Table of Contents", styles["SectionTitle"]))
    story.append(hr())
    toc_items = [
        ("1", "Project Overview & Objectives"),
        ("2", "System Architecture"),
        ("3", "Setup & Running Guide"),
        ("4", "Technology Stack & Justification"),
        ("5", "Protocol Deep-Dive: A2A & MCP"),
        ("6", "Microservices & Agents"),
        ("7", "MCP Server & Tool Registry"),
        ("8", "LLM Integration (Groq)"),
        ("9", "Frontend & User Interface"),
        ("10", "API Reference"),
        ("11", "Data Flow & Workflow Execution"),
        ("12", "Testing Strategy"),
        ("13", "Security & Production Considerations"),
        ("14", "Interview Talking Points"),
        ("15", "Demo Walkthrough Script"),
        ("16", "FAQ & Anticipated Questions"),
    ]
    for num, title in toc_items:
        story.append(Paragraph(f"<b>Section {num}</b> — {title}", styles["TOCEntry"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 1 — PROJECT OVERVIEW
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("1. Project Overview & Objectives", styles["SectionTitle"]))
    story.append(hr())
    story.append(Paragraph(
        "This project is a <b>production-grade, multi-agent healthcare data processing system</b> "
        "built on three cutting-edge open standards:", styles["Body"]))

    story.append(bullet("<b>A2A (Agent-to-Agent)</b> — Google's open protocol for inter-agent communication and discovery"))
    story.append(bullet("<b>MCP (Model Context Protocol)</b> — Anthropic's standard for LLM tool integration"))
    story.append(bullet("<b>Groq LLM</b> — Ultra-fast inference API powering dynamic planning and clinical analysis"))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("<b>Key Objectives:</b>", styles["Body"]))
    for item in numbered([
        "Demonstrate a working multi-agent system with real protocol implementations (not mocks)",
        "Process healthcare documents (PDF, Excel, text) through specialized autonomous agents",
        "Show dynamic LLM-powered planning where the system decides which agents and tools to use",
        "Provide real-time visibility via Server-Sent Events (SSE) streaming to the frontend",
        "Implement human-in-the-loop approval gates for sensitive healthcare decisions",
        "Generate clinical briefs with AI-enhanced analysis",
        "Track LLM token usage and cost estimation across all agents",
    ]):
        story.append(item)

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "<b>What makes this different:</b> Unlike typical chatbot demos, this system uses "
        "<i>multiple specialized agents</i> that discover each other at runtime, negotiate task "
        "delegation via standardized protocols, and execute a dynamically-generated DAG "
        "(Directed Acyclic Graph) of steps — with parallel execution where possible.", styles["Callout"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 2 — SYSTEM ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. System Architecture", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("<b>High-Level Architecture Diagram</b>", styles["SubSection"]))
    arch_text = (
        "┌─────────────────────────────────────────────────────────────────┐\n"
        "│   FRONTEND  (Next.js 14 + Tailwind)        :3000              │\n"
        "│   ┌──────────────┐ ┌───────────────────────┐                  │\n"
        "│   │ Trace Panel  │ │ Summary / JSON Output  │    ◄── SSE     │\n"
        "│   └──────────────┘ └───────────────────────┘                  │\n"
        "└───────────────────────────┬─────────────────────────────────────┘\n"
        "                           │ POST /workflow/stream\n"
        "┌───────────────────────────▼─────────────────────────────────────┐\n"
        "│   ORCHESTRATOR  (FastAPI)                   :8000              │\n"
        "│   ┌──────────┐ ┌─────────┐ ┌──────────────┐                  │\n"
        "│   │ Registry │ │ Planner │ │ DAG Executor  │                  │\n"
        "│   └──────────┘ └─────────┘ └──────────────┘                  │\n"
        "└────┬──────────────┬──────────────┬──────────────┬─────────────┘\n"
        "     │ A2A          │ A2A          │ A2A          │ MCP\n"
        "┌────▼────┐  ┌──────▼─────┐  ┌─────▼──────┐  ┌───▼──────────┐\n"
        "│ READER  │  │ ANALYZER   │  │ SUMMARIZER │  │  MCP SERVER  │\n"
        "│  :8001  │  │   :8002    │  │   :8003    │  │    :8004     │\n"
        "│ PDF,XLS │  │ Questions  │  │ Summaries  │  │  8 Tools     │\n"
        "│ TXT     │  │ Keywords   │  │ Clinical   │  │  read_*      │\n"
        "│         │  │ Analysis   │  │ Briefs     │  │  extract_*   │\n"
        "└────┬────┘  └─────┬──────┘  └─────┬──────┘  │  summarize_* │\n"
        "     │             │               │         │  analyze_*   │\n"
        "     └─────────────┴───────────────┘         │  llm_enhance │\n"
        "                   │                         └──────────────┘\n"
        "          ┌────────▼────────┐\n"
        "          │  Redis  :6379  │\n"
        "          │  Shared Memory │\n"
        "          └────────────────┘"
    )
    story.append(code_block(arch_text))

    story.append(Paragraph("<b>Service Topology</b>", styles["SubSection"]))
    story.append(make_table(
        ["Service", "Port", "Protocol", "Responsibility"],
        [
            ["Orchestrator",    "8000", "FastAPI + SSE",       "Planning, DAG execution, coordination"],
            ["Reader Agent",    "8001", "FastAPI + A2A",       "PDF / Excel / Text file reading"],
            ["Analyzer Agent",  "8002", "FastAPI + A2A",       "Question extraction, keywords, data analysis"],
            ["Summarizer Agent","8003", "FastAPI + A2A",       "Text summarization, clinical brief generation"],
            ["MCP Server",      "8004", "FastMCP HTTP",        "8 tool endpoints (read, extract, analyze, enhance)"],
            ["Frontend",        "3000", "Next.js 14 SSE",      "Real-time UI with streaming trace"],
            ["Redis",           "6379", "Redis Protocol",      "Shared memory, workflow state (1hr TTL)"],
        ],
        col_widths=[1.2*inch, 0.6*inch, 1.2*inch, 3.2*inch],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 3 — SETUP & RUNNING GUIDE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Setup & Running Guide", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("3.1 Prerequisites", styles["SubSection"]))
    story.append(make_table(
        ["Requirement", "Version", "Purpose"],
        [
            ["Docker Desktop", "≥ 4.x", "Container runtime for all services"],
            ["Docker Compose", "≥ 2.x", "Multi-container orchestration (bundled with Docker Desktop)"],
            ["Git",            "any",   "Clone the repository"],
            ["Groq API Key",   "—",     "Free at console.groq.com — required for LLM features"],
        ],
        col_widths=[1.5*inch, 0.9*inch, 3.8*inch],
    ))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(
        "<b>No Python or Node.js installation needed on the host machine.</b> "
        "Everything runs inside Docker containers.", styles["Callout"]))

    story.append(Paragraph("3.2 Quick Start (Docker — Recommended)", styles["SubSection"]))
    story.append(Paragraph("<b>Step 1: Clone the repository</b>", styles["SubSubSection"]))
    story.append(code_block("git clone &lt;repository-url&gt;\ncd philips_3.1"))

    story.append(Paragraph("<b>Step 2: Configure environment</b>", styles["SubSubSection"]))
    story.append(code_block(
        "# Open .env file and set your Groq API key:\n"
        "GROQ_API_KEY=gsk_your_api_key_here\n"
        "GROQ_DEFAULT_MODEL=llama-3.3-70b-versatile\n"
        "GROQ_FALLBACK_MODEL=llama-3.1-8b-instant"
    ))
    story.append(Paragraph(
        "Get a free API key at <font color='#1565c0'>console.groq.com</font>. "
        "The free tier provides generous rate limits for demo purposes.", styles["Body"]))

    story.append(Paragraph("<b>Step 3: Build and start all services</b>", styles["SubSubSection"]))
    story.append(code_block("docker-compose up --build -d"))
    story.append(Paragraph("This single command:", styles["Body"]))
    story.append(bullet("Builds 6 Docker images (Python 3.11 + Node 20)"))
    story.append(bullet("Starts Redis with health checks"))
    story.append(bullet("Launches MCP Server, 3 Agent microservices, Orchestrator, and Frontend"))
    story.append(bullet("Sets up inter-service networking automatically"))
    story.append(bullet("Creates a shared <font name='Courier' size='9.5'>uploads</font> volume for file sharing"))

    story.append(Paragraph("<b>Step 4: Verify all services are running</b>", styles["SubSubSection"]))
    story.append(code_block(
        "docker-compose ps\n\n"
        "# Expected output: all 7 services showing 'Up'\n"
        "# Verify orchestrator health:\n"
        "curl http://localhost:8000/health\n\n"
        "# List discovered agents:\n"
        "curl http://localhost:8000/agents\n\n"
        "# List available MCP tools:\n"
        "curl http://localhost:8000/tools"
    ))

    story.append(Paragraph("<b>Step 5: Open the UI</b>", styles["SubSubSection"]))
    story.append(code_block("# Open in your browser:\nhttp://localhost:3000"))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("<b>Step 6: Run your first workflow</b>", styles["SubSubSection"]))
    for item in numbered([
        'In the Goal field, type: <i>"Read and summarize sample_data/clinical_review.txt"</i>',
        'Click <b>Execute Workflow</b>',
        'Watch the <b>Trace Panel</b> (bottom) show real-time step execution',
        'See results appear in the <b>Summary</b> tab with formatted clinical brief',
        'Switch to <b>JSON</b> tab to see raw API response',
    ]):
        story.append(item)

    story.append(Paragraph("3.3 Manual Setup (Without Docker)", styles["SubSection"]))
    story.append(Paragraph("For development or debugging, you can run each service individually:", styles["Body"]))
    story.append(code_block(
        "# Terminal 1 — Redis (still needs Docker or a local install)\n"
        "docker run -d -p 6379:6379 redis:7-alpine\n\n"
        "# Terminal 2 — Install Python dependencies\n"
        "pip install -r requirements.txt\n\n"
        "# Terminal 3 — MCP Server\n"
        "python -m mcp_server.server\n\n"
        "# Terminal 4 — Reader Agent\n"
        "python -m agents.reader.main\n\n"
        "# Terminal 5 — Analyzer Agent\n"
        "python -m agents.analyzer.main\n\n"
        "# Terminal 6 — Summarizer Agent\n"
        "python -m agents.summarizer.main\n\n"
        "# Terminal 7 — Orchestrator\n"
        "python -m orchestrator.main\n\n"
        "# Terminal 8 — Frontend\n"
        "cd frontend &amp;&amp; npm install &amp;&amp; npm run dev"
    ))

    story.append(Paragraph("3.4 Useful Docker Commands", styles["SubSection"]))
    story.append(make_table(
        ["Command", "Purpose"],
        [
            ["docker-compose up --build -d",           "Build and start all (background)"],
            ["docker-compose ps",                       "Check service status"],
            ["docker-compose logs -f orchestrator",     "Stream orchestrator logs"],
            ["docker-compose logs -f --tail 50",        "Stream last 50 lines from all services"],
            ["docker-compose down",                     "Stop all services"],
            ["docker-compose down -v",                  "Stop + remove volumes (clean slate)"],
            ["docker-compose build --no-cache SERVICE", "Force full rebuild of one service"],
            ["docker exec -it <container> bash",        "Shell into a running container"],
        ],
        col_widths=[3*inch, 3.2*inch],
    ))

    story.append(Paragraph("3.5 Troubleshooting", styles["SubSection"]))
    story.append(make_table(
        ["Issue", "Solution"],
        [
            ["Port already in use",       "Change port in docker-compose.yml or stop conflicting service"],
            ["500 Internal Server Error",  "Check logs: docker-compose logs orchestrator --tail 30"],
            ["Model decommissioned error", "Update GROQ_FALLBACK_MODEL in .env to llama-3.1-8b-instant"],
            ["Frontend can't reach API",   "Frontend auto-detects host via window.location — ensure port 8000 is exposed"],
            ["MCP connection refused",     "Ensure mcp-server started before agents (docker-compose handles this)"],
            ["Rate limit errors (429)",    "System has automatic retry with exponential backoff; wait and retry"],
        ],
        col_widths=[1.8*inch, 4.4*inch],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 4 — TECHNOLOGY STACK & JUSTIFICATION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Technology Stack & Justification", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph(
        "Every technology choice was made deliberately. Below is the full stack with "
        "reasoning for each selection.", styles["Body"]))

    story.append(Paragraph("4.1 Backend Technologies", styles["SubSection"]))
    story.append(make_table(
        ["Technology", "Role", "Why This Over Alternatives"],
        [
            ["Python 3.11",      "Service language",
             "Required by MCP SDK (mcp package). Async support via asyncio. "
             "Mature healthcare/data science ecosystem."],
            ["FastAPI",          "Web framework",
             "Async-native, auto-generated OpenAPI docs, Pydantic validation, "
             "SSE support. Chosen over Flask (sync) and Django (heavyweight)."],
            ["Groq (llama-3.3-70b)",  "LLM inference",
             "Sub-second latency vs OpenAI's 2-5s. Free tier available. "
             "Competitive accuracy. Chosen over OpenAI (cost/latency) and "
             "local models (hardware requirements)."],
            ["Redis 7",          "Shared memory",
             "Sub-ms latency, built-in TTL for automatic cleanup, "
             "lightweight. Chosen over PostgreSQL (overkill) and in-memory "
             "dicts (not shared across containers)."],
            ["MCP Python SDK",   "Tool protocol",
             "Official Anthropic SDK. Standardized tool discovery and "
             "invocation. Streamable HTTP transport. Industry-standard."],
            ["httpx",            "HTTP client",
             "Async-native, HTTP/2 support. Required for A2A inter-agent "
             "communication. Chosen over requests (sync-only)."],
            ["PyPDF2 + openpyxl","File parsing",
             "Lightweight, no system dependencies. PDF and Excel reading "
             "without heavy libraries like Apache POI or Tesseract."],
        ],
        col_widths=[1.2*inch, 1*inch, 4*inch],
    ))

    story.append(Paragraph("4.2 Frontend Technologies", styles["SubSection"]))
    story.append(make_table(
        ["Technology", "Role", "Why This Over Alternatives"],
        [
            ["Next.js 14",      "React framework",
             "App Router with SSR, built-in API routes, excellent DX. "
             "Chosen over plain React (no SSR) and Vue (team familiarity)."],
            ["Tailwind CSS",    "Styling",
             "Utility-first, rapid prototyping, consistent dark theme. "
             "Chosen over CSS modules (verbose) and Material UI (opinionated)."],
            ["react-markdown",  "Markdown rendering",
             "Renders clinical briefs with proper formatting (headers, "
             "lists, bold). Lightweight alternative to full rich text editors."],
            ["Server-Sent Events", "Real-time streaming",
             "Simpler than WebSockets for one-way server→client streaming. "
             "Native browser support. Perfect for workflow progress updates."],
        ],
        col_widths=[1.4*inch, 1*inch, 3.8*inch],
    ))

    story.append(Paragraph("4.3 Infrastructure", styles["SubSection"]))
    story.append(make_table(
        ["Technology", "Role", "Why This Over Alternatives"],
        [
            ["Docker Compose",  "Orchestration",
             "Single command starts 7 services. Isolated networking. "
             "Chosen over Kubernetes (overkill for demo) and manual setup (error-prone)."],
            ["Named Volumes",   "File sharing",
             "Shared 'uploads' volume across all containers. Persistent "
             "across restarts. Chosen over bind mounts (path issues on Windows)."],
            ["Bridge Network",  "Inter-service comms",
             "Services reference each other by name (e.g., mcp-server:8004). "
             "Automatic DNS. No manual IP management."],
        ],
        col_widths=[1.4*inch, 1.2*inch, 3.6*inch],
    ))

    story.append(Paragraph("4.4 Why NOT Other Options", styles["SubSection"]))
    story.append(make_table(
        ["Rejected Option", "Reason"],
        [
            ["LangChain / LangGraph",  "Heavy abstraction layer. We wanted to demonstrate raw protocol "
                                        "implementation (A2A + MCP) without framework lock-in."],
            ["OpenAI GPT-4",            "Higher latency (2-5s vs Groq's <1s), higher cost, and API key "
                                        "costs for demos. Groq's free tier is sufficient."],
            ["Kubernetes",              "Over-engineered for a demo. Docker Compose achieves the same "
                                        "multi-service orchestration with zero infrastructure overhead."],
            ["WebSockets",              "Overkill for one-way streaming. SSE is simpler, lighter, and "
                                        "has native browser support without library dependencies."],
            ["MongoDB",                 "No complex queries needed. Redis's key-value model with TTL "
                                        "is perfect for ephemeral workflow state."],
            ["gRPC",                    "A2A and MCP both use HTTP/JSON. Adding gRPC would introduce "
                                        "protocol mismatch and proto compilation overhead."],
        ],
        col_widths=[1.6*inch, 4.6*inch],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 5 — PROTOCOL DEEP-DIVE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Protocol Deep-Dive: A2A & MCP", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("5.1 A2A (Agent-to-Agent) Protocol — Google", styles["SubSection"]))
    story.append(Paragraph(
        "A2A is Google's open standard for agent interoperability. It enables agents built by "
        "different teams or organizations to discover and communicate with each other without "
        "tight coupling.", styles["Body"]))

    story.append(Paragraph("<b>How we implement A2A:</b>", styles["SubSubSection"]))
    story.append(bullet("<b>Agent Cards</b>: Each agent exposes <font name='Courier'>GET /.well-known/agent.json</font> — a JSON document describing the agent's name, capabilities, and supported input/output modes."))
    story.append(bullet("<b>Task Sending</b>: <font name='Courier'>POST /tasks/send</font> — the orchestrator sends a task to an agent with a structured payload (tool name, inputs, context from prior steps)."))
    story.append(bullet("<b>Task Streaming</b>: <font name='Courier'>POST /tasks/stream</font> — alternative endpoint returning SSE for long-running tasks."))
    story.append(bullet("<b>Discovery</b>: At startup, the orchestrator fetches agent cards from all configured agent URLs and caches their capabilities."))

    story.append(Paragraph("<b>Agent Card Example:</b>", styles["SubSubSection"]))
    story.append(code_block(
        '{\n'
        '  "name": "reader",\n'
        '  "url": "http://reader-agent:8001",\n'
        '  "description": "Reads PDF, Excel, and text files",\n'
        '  "capabilities": [\n'
        '    {"name": "file_reading", "description": "Read any file type"},\n'
        '    {"name": "pdf_reading",  "description": "Extract text from PDF"}\n'
        '  ],\n'
        '  "inputModes": ["application/json"],\n'
        '  "outputModes": ["application/json"]\n'
        '}'
    ))

    story.append(Paragraph("<b>A2A Task Flow:</b>", styles["SubSubSection"]))
    story.append(code_block(
        "Orchestrator                    Agent\n"
        "    │                             │\n"
        "    │── GET /.well-known/agent.json ──▶│  (Discovery)\n"
        "    │◀── AgentCard JSON ──────────│\n"
        "    │                             │\n"
        "    │── POST /tasks/send ─────────▶│  (Task Execution)\n"
        "    │   {id, correlation_id,      │\n"
        "    │    input: {tool, args...}}   │\n"
        "    │                             │\n"
        "    │◀── {status, output} ────────│  (Result)\n"
        "    │                             │"
    ))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("5.2 MCP (Model Context Protocol) — Anthropic", styles["SubSection"]))
    story.append(Paragraph(
        "MCP is Anthropic's protocol for giving LLMs access to external tools in a standardized way. "
        "Our MCP server exposes 8 tools that any agent can discover and call.", styles["Body"]))

    story.append(Paragraph("<b>How we implement MCP:</b>", styles["SubSubSection"]))
    story.append(bullet("<b>Server</b>: Built with <font name='Courier'>FastMCP</font> from the official <font name='Courier'>mcp</font> Python SDK"))
    story.append(bullet("<b>Transport</b>: Streamable HTTP at <font name='Courier'>http://mcp-server:8004/mcp</font>"))
    story.append(bullet("<b>Tool Registration</b>: <font name='Courier'>@mcp.tool()</font> decorator with typed Python arguments"))
    story.append(bullet("<b>Client</b>: Agents connect via <font name='Courier'>mcp.client.streamable_http_client</font>, call <font name='Courier'>session.call_tool(name, args)</font>"))

    story.append(Paragraph("<b>MCP Tool Invocation Flow:</b>", styles["SubSubSection"]))
    story.append(code_block(
        "Agent                           MCP Server\n"
        "  │                                │\n"
        "  │── streamable_http_client() ──▶ │  (Connect)\n"
        "  │── session.list_tools() ──────▶ │  (Discover)\n"
        "  │◀── [{name, description, ...}]──│\n"
        "  │                                │\n"
        "  │── session.call_tool(           │\n"
        "  │     'summarize_text',          │  (Invoke)\n"
        "  │     {'text': '...', 'num': 5}) │\n"
        "  │◀── {summary, method, ...} ─────│  (Result)\n"
        "  │                                │"
    ))

    story.append(Paragraph("5.3 Why Both Protocols?", styles["SubSubSection"]))
    story.append(make_table(
        ["Aspect", "A2A", "MCP"],
        [
            ["Purpose",     "Agent ↔ Agent communication", "Agent ↔ Tool communication"],
            ["Analogy",     "Agents talking to each other",  "Agents using tools"],
            ["Discovery",   "Agent Cards at /.well-known/",  "list_tools() method"],
            ["Creator",     "Google",                        "Anthropic"],
            ["Transport",   "HTTP REST + SSE",               "Streamable HTTP"],
            ["In our system","Orchestrator → Agent routing",  "Agent → MCP tool execution"],
        ],
        col_widths=[1*inch, 2.5*inch, 2.7*inch],
    ))

    story.append(Paragraph(
        "<b>Key insight:</b> A2A handles <i>who</i> does the work (agent routing), while MCP handles "
        "<i>how</i> the work gets done (tool execution). Together they enable a fully decoupled, "
        "protocol-standard multi-agent system.", styles["Callout"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 6 — MICROSERVICES & AGENTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Microservices & Agents", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("6.1 Orchestrator (Port 8000)", styles["SubSection"]))
    story.append(Paragraph(
        "The brain of the system. Receives user goals, generates execution plans via Groq, "
        "and coordinates agent execution.", styles["Body"]))
    story.append(Paragraph("<b>Key Components:</b>", styles["SubSubSection"]))
    story.append(bullet("<b>Agent Registry</b>: Discovers agents at startup by fetching their A2A agent cards"))
    story.append(bullet("<b>Planner</b>: Sends goal + agent capabilities + tool list to Groq → receives a DAG execution plan"))
    story.append(bullet("<b>DAG Executor</b>: Iteratively finds ready steps (dependencies met), executes them in parallel via <font name='Courier'>asyncio.gather()</font>, passes context between dependent steps"))
    story.append(bullet("<b>SSE Broadcaster</b>: Streams trace events to the frontend in real-time"))
    story.append(bullet("<b>File Upload Handler</b>: Receives uploaded files, stores in shared volume"))

    story.append(Paragraph("6.2 Reader Agent (Port 8001)", styles["SubSection"]))
    story.append(Paragraph(
        "Specializes in reading and extracting raw content from files.", styles["Body"]))
    story.append(bullet("Supports: PDF (via PyPDF2), Excel (via openpyxl), plain text/CSV"))
    story.append(bullet("Automatically selects the correct MCP tool based on file extension"))
    story.append(bullet("Stores extracted content in Redis for downstream agents"))
    story.append(bullet("Returns: file content, character count, line count, file metadata"))

    story.append(Paragraph("6.3 Analyzer Agent (Port 8002)", styles["SubSection"]))
    story.append(Paragraph(
        "Performs analytical operations on text and data.", styles["Body"]))
    story.append(bullet("<b>Question Extraction</b>: Finds embedded questions using regex (sentences ending with '?', question-word patterns)"))
    story.append(bullet("<b>Keyword Extraction</b>: TF-based keyword ranking with stopword filtering"))
    story.append(bullet("<b>Tabular Data Analysis</b>: Statistical analysis (min, max, mean, std dev, anomaly detection, trend analysis) for Excel data"))
    story.append(bullet("<b>Context Aggregation</b>: Collects text from all prior step outputs to analyze holistically"))

    story.append(Paragraph("6.4 Summarizer Agent (Port 8003)", styles["SubSection"]))
    story.append(Paragraph(
        "Generates summaries and AI-enhanced clinical briefs.", styles["Body"]))
    story.append(bullet("<b>Extractive Summary</b>: TF-scoring to select top-N most important sentences"))
    story.append(bullet("<b>Clinical Brief</b>: Groq LLM enhances the summary with clinical implications, evidence-based insights, and actionable recommendations"))
    story.append(bullet("<b>Analysis Integration</b>: Incorporates outputs from analyzer steps into the brief"))
    story.append(bullet("Returns: extractive summary + clinical brief + token usage metrics"))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 7 — MCP SERVER & TOOLS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("7. MCP Server & Tool Registry", styles["SectionTitle"]))
    story.append(hr())
    story.append(Paragraph(
        "The MCP server exposes 8 tools via the Model Context Protocol. Any agent can discover "
        "and invoke these tools at runtime.", styles["Body"]))

    story.append(make_table(
        ["Tool Name", "Input", "Output", "Description"],
        [
            ["read_pdf",          "file_path",           "content, pages, chars",         "Extract text from PDF files"],
            ["read_excel",        "file_path",           "sheets{headers, rows}",         "Read Excel workbooks with all sheets"],
            ["read_text",         "file_path",           "content, chars, lines",         "Read plain text / CSV files"],
            ["extract_questions", "text",                "questions[], count",            "Find embedded questions via regex"],
            ["summarize_text",    "text, num_sentences", "summary, method, sentences",    "Extractive TF-based summarization"],
            ["extract_keywords",  "text, top_n",         "keywords[], frequencies",       "TF-based keyword ranking"],
            ["analyze_tabular_data", "headers, rows",    "column_stats, insights",        "Statistical analysis + anomaly detection"],
            ["llm_enhance",       "text, context, task_type", "enhanced_text, tokens",    "Groq LLM clinical enhancement"],
        ],
        col_widths=[1.3*inch, 1.1*inch, 1.5*inch, 2.3*inch],
    ))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("<b>Tool Registration Pattern:</b>", styles["SubSubSection"]))
    story.append(code_block(
        "from mcp.server.fastmcp import FastMCP\n\n"
        "mcp = FastMCP('healthcare-tools')\n\n"
        "@mcp.tool()\n"
        "async def summarize_text(text: str, num_sentences: int = 5) -&gt; dict:\n"
        "    '''Summarize the given text using extractive TF scoring.'''\n"
        "    # ... implementation ...\n"
        "    return {'summary': result, 'method': 'extractive_tf'}"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 8 — LLM INTEGRATION
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("8. LLM Integration (Groq)", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("8.1 GroqAdapter — Centralized LLM Interface", styles["SubSection"]))
    story.append(Paragraph(
        "All LLM calls go through <font name='Courier'>shared/llm_adapter.py</font>, which provides "
        "retry logic, rate-limit handling, token tracking, and model fallback.", styles["Body"]))

    story.append(make_table(
        ["Feature", "Implementation"],
        [
            ["Primary Model",        "llama-3.3-70b-versatile (Meta's latest, 70B parameters)"],
            ["Fallback Model",        "llama-3.1-8b-instant (faster, smaller, used on rate limits)"],
            ["Rate Limit Handling",   "Exponential backoff: 2s → 4s → 8s delays on 429 errors"],
            ["Model Switching",       "After 2nd retry, automatically switches to fallback model"],
            ["Token Tracking",        "Cumulative input/output tokens tracked per adapter instance"],
            ["Cost Estimation",       "~$0.05/1M input tokens, ~$0.08/1M output tokens"],
            ["JSON Mode",             "response_format={'type': 'json_object'} for structured output"],
            ["Clinical Enhancement",  "Specialized method with clinical system prompt"],
        ],
        col_widths=[1.5*inch, 4.7*inch],
    ))

    story.append(Paragraph("8.2 Where Groq Is Used", styles["SubSection"]))
    story.append(bullet("<b>Planner</b>: Generates the DAG execution plan from natural language goals (JSON mode)"))
    story.append(bullet("<b>Summarizer</b>: Creates AI-enhanced clinical briefs from extractive summaries"))
    story.append(bullet("<b>Analyzer</b>: Interprets statistical analysis results in natural language"))
    story.append(bullet("<b>MCP llm_enhance tool</b>: General-purpose LLM enhancement available to any agent"))

    story.append(Paragraph("8.3 Why Groq Over OpenAI / Anthropic?", styles["SubSubSection"]))
    story.append(make_table(
        ["Factor", "Groq", "OpenAI GPT-4", "Anthropic Claude"],
        [
            ["Latency",      "<1 second",    "2-5 seconds",   "2-4 seconds"],
            ["Cost",          "Free tier",    "$30+/1M tokens", "$15+/1M tokens"],
            ["Model Quality", "Competitive (Llama 3.3 70B)", "Best (GPT-4o)", "Excellent (Claude 3.5)"],
            ["JSON Mode",     "Supported",    "Supported",      "Supported"],
            ["Rate Limits",   "Generous free tier", "Pay-per-use", "Pay-per-use"],
            ["For Demo",      "Ideal ✓",    "Too expensive",   "Too expensive"],
        ],
        col_widths=[1.1*inch, 1.4*inch, 1.5*inch, 1.5*inch],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 9 — FRONTEND
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("9. Frontend & User Interface", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("9.1 Layout", styles["SubSection"]))
    story.append(code_block(
        "┌──────────────────────────────────────────────────────────┐\n"
        "│  HEADER: Token Usage (input↑  output↓  cost)           │\n"
        "├────────────────┬─────────────────────────────────────────┤\n"
        "│ INPUT PANEL    │  OUTPUT PANEL                          │\n"
        "│                │  ┌─────────┐ ┌──────┐                 │\n"
        "│ • Goal input   │  │ Summary │ │ JSON │  ← Tab Switch   │\n"
        "│ • File upload  │  └─────────┘ └──────┘                 │\n"
        "│ • File chips   │                                        │\n"
        "│ • [Execute]    │  Step-by-step results:                 │\n"
        "│                │  [reader → read_text]                  │\n"
        "│                │  [analyzer → extract_questions]        │\n"
        "│                │  [summarizer → summarize_text]         │\n"
        "├────────────────┴─────────────────────────────────────────┤\n"
        "│  TRACE PANEL (auto-scrolling real-time execution log)  │\n"
        "└──────────────────────────────────────────────────────────┘"
    ))

    story.append(Paragraph("9.2 Key Features", styles["SubSection"]))
    story.append(bullet("<b>Real-Time Streaming</b>: SSE connection shows step-by-step execution as it happens"))
    story.append(bullet("<b>Dual Output View</b>: Summary tab (formatted, human-readable) and JSON tab (raw data)"))
    story.append(bullet("<b>Smart Rendering</b>: Detects output type and renders appropriately — numbered lists for questions, tag chips for keywords, Markdown for clinical briefs, code preview for file content"))
    story.append(bullet("<b>File Upload</b>: Drag-and-drop or click to upload files, shown as removable chips"))
    story.append(bullet("<b>Token Counter</b>: Header shows total input/output tokens and estimated cost"))
    story.append(bullet("<b>Step Badges</b>: Each result card shows which agent and tool produced it"))
    story.append(bullet("<b>Dark Theme</b>: Professional healthcare UI with Tailwind CSS"))

    story.append(Paragraph("9.3 SSE Event Types", styles["SubSection"]))
    story.append(make_table(
        ["Event Type", "Data", "UI Action"],
        [
            ["start",    "correlation_id",              "Set workflow ID, clear previous results"],
            ["plan",     "steps[]",                     "Store plan for badge rendering"],
            ["trace",    "step_id, agent, tool, status","Append to trace panel, auto-scroll"],
            ["complete", "results{}, token_usage",      "Render results in Summary/JSON tabs"],
            ["error",    "message",                     "Show error in trace panel"],
        ],
        col_widths=[0.9*inch, 2*inch, 3.3*inch],
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 10 — API REFERENCE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("10. API Reference", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("10.1 Orchestrator Endpoints (Port 8000)", styles["SubSection"]))
    story.append(make_table(
        ["Method", "Endpoint", "Input", "Output"],
        [
            ["GET",  "/health",                  "—",                               '{"status": "healthy", ...}'],
            ["GET",  "/agents",                  "—",                               '{"agents": {name: AgentCard}}'],
            ["GET",  "/tools",                   "—",                               '{"tools": [{name, desc}]}'],
            ["POST", "/upload",                  "multipart/form-data (file)",       '{"filename", "path", "size"}'],
            ["POST", "/workflow",                '{"goal", "files[]"}',             '{"correlation_id", "results", "trace", "token_usage", "plan"}'],
            ["POST", "/workflow/stream",         '{"goal", "files[]"}',             "SSE stream (start → plan → trace* → complete)"],
            ["POST", "/workflow/approve",        '{"step_id", "approved", "cid"}',  '{"status": "approved/rejected"}'],
            ["GET",  "/workflow/{cid}/trace",    "—",                               '{"trace": [TraceEvent]}'],
            ["GET",  "/workflow/{cid}/results",  "—",                               '{"results": {step_id: data}}'],
        ],
        col_widths=[0.6*inch, 1.7*inch, 1.7*inch, 2.2*inch],
    ))

    story.append(Paragraph("10.2 Agent Endpoints (Ports 8001-8003)", styles["SubSection"]))
    story.append(make_table(
        ["Method", "Endpoint", "Purpose"],
        [
            ["GET",  "/health",                   "Service health check"],
            ["GET",  "/.well-known/agent.json",    "A2A agent card (discovery)"],
            ["POST", "/tasks/send",                "Execute a task (sync, JSON response)"],
            ["POST", "/tasks/stream",              "Execute a task (SSE streaming)"],
        ],
        col_widths=[0.6*inch, 2.2*inch, 3.4*inch],
    ))

    story.append(Paragraph("10.3 Task Payload (A2A Protocol)", styles["SubSubSection"]))
    story.append(code_block(
        "// Request: POST /tasks/send\n"
        "{\n"
        '  "id": "task-uuid",\n'
        '  "correlation_id": "workflow-uuid",\n'
        '  "input": {\n'
        '    "tool": "read_text",\n'
        '    "file_path": "sample_data/sample.txt",\n'
        '    "step_id": "step_1",\n'
        '    "context": {}\n'
        "  }\n"
        "}\n\n"
        "// Response\n"
        "{\n"
        '  "id": "task-uuid",\n'
        '  "status": "completed",\n'
        '  "output": {"content": "...", "chars": 5599, "lines": 125}\n'
        "}"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 11 — DATA FLOW
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("11. Data Flow & Workflow Execution", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("11.1 End-to-End Workflow (Example)", styles["SubSection"]))
    story.append(Paragraph(
        '<b>User Goal:</b> <i>"Read and summarize the clinical review document"</i>', styles["Body"]))

    for item in numbered([
        "<b>Frontend → Orchestrator</b>: POST /workflow/stream with goal and file paths",
        "<b>Orchestrator → Groq</b>: Sends goal + agent capabilities + tool list → receives DAG plan",
        "<b>Plan Generated</b>: step_1 (reader/read_text) → step_2 (analyzer/extract_questions, depends on step_1) → step_3 (summarizer/summarize_text, depends on step_1)",
        "<b>DAG Execution Round 1</b>: step_1 has no dependencies → runs immediately. Orchestrator POST to Reader Agent via A2A. Reader calls MCP read_text tool. Content stored in Redis.",
        "<b>DAG Execution Round 2</b>: step_2 and step_3 both depend on step_1 (now complete) → run <i>in parallel</i> via asyncio.gather(). Analyzer receives file content as context, calls MCP extract_questions. Summarizer receives content, calls MCP summarize_text + llm_enhance.",
        "<b>Results Aggregated</b>: All step outputs compiled. Token usage summed across agents.",
        "<b>SSE Complete Event</b>: Final results + trace + token usage streamed to frontend.",
        "<b>Frontend Renders</b>: Summary tab shows file preview, extracted questions, and AI-enhanced clinical brief with Markdown formatting.",
    ]):
        story.append(item)

    story.append(Paragraph("11.2 Context Passing Between Steps", styles["SubSection"]))
    story.append(Paragraph(
        "When a step depends on previous steps, the orchestrator automatically passes the outputs "
        "of completed dependencies as <font name='Courier'>context</font> in the task input. "
        "Agents prioritize context over their own inputs, ensuring data flows correctly through "
        "the pipeline.", styles["Body"]))
    story.append(code_block(
        "# In orchestrator _execute_step():\n"
        "context = {}\n"
        "for dep_id in step.depends_on:\n"
        "    if dep_id in all_results:\n"
        "        context[dep_id] = all_results[dep_id]\n\n"
        "task_input = {**step.inputs}       # Planner-provided inputs\n"
        "task_input['tool'] = step.tool\n"
        "task_input['step_id'] = step.step_id\n"
        "task_input['context'] = context    # Overrides any 'context' from inputs"
    ))

    story.append(Paragraph("11.3 Parallel Execution", styles["SubSection"]))
    story.append(Paragraph(
        "The DAG executor identifies steps whose dependencies are all satisfied and runs them "
        "concurrently. This significantly reduces total workflow time.", styles["Body"]))
    story.append(code_block(
        "# Example: step_2 and step_3 both depend on step_1\n"
        "# After step_1 completes, both run simultaneously:\n\n"
        "ready = [step_2, step_3]\n"
        "tasks = [_execute_step(s, ...) for s in ready]\n"
        "results = await asyncio.gather(*tasks, return_exceptions=True)"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 12 — TESTING
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("12. Testing Strategy", styles["SectionTitle"]))
    story.append(hr())

    story.append(make_table(
        ["Test File", "Scope", "Key Tests"],
        [
            ["test_groq_adapter.py",  "Unit",        "Token tracking, usage calculation, cost estimation"],
            ["test_mcp_server.py",    "Unit",        "All 8 MCP tools: file reading, extraction, analysis, summarization"],
            ["test_orchestrator.py",  "Unit",        "Agent card validation, registry search, DAG ordering"],
            ["test_planner.py",       "Unit + Live", "PlanStep/ExecutionPlan models, live plan generation (with API key)"],
            ["test_agent_cards.py",   "Unit",        "Validates all agent_card.json files: fields, capabilities"],
            ["test_agents.py",        "Integration", "Agent endpoint testing"],
        ],
        col_widths=[1.5*inch, 0.8*inch, 3.9*inch],
    ))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("<b>Running Tests:</b>", styles["SubSubSection"]))
    story.append(code_block(
        "# Run all tests\n"
        "python -m pytest tests/ -v\n\n"
        "# Run with coverage\n"
        "python -m pytest tests/ -v --cov=shared --cov=orchestrator\n\n"
        "# Skip live tests (no API key needed)\n"
        "python -m pytest tests/ -v -k 'not live'"
    ))
    story.append(Paragraph("51 tests pass, covering models, tools, adapters, and agent cards.", styles["Body"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 13 — SECURITY
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("13. Security & Production Considerations", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("<b>Current Security Measures:</b>", styles["SubSubSection"]))
    story.append(bullet("API keys stored in <font name='Courier'>.env</font> file, never committed to version control"))
    story.append(bullet("Inter-service communication via Docker bridge network (not exposed externally)"))
    story.append(bullet("Redis has 1-hour TTL for automatic cleanup of sensitive workflow data"))
    story.append(bullet("Input validation via Pydantic models on all endpoints"))
    story.append(bullet("File upload limited to shared Docker volume (sandboxed)"))
    story.append(bullet("CORS configured for frontend origin only"))

    story.append(Paragraph("<b>Production Recommendations:</b>", styles["SubSubSection"]))
    story.append(bullet("Add JWT/OAuth2 authentication on all endpoints"))
    story.append(bullet("Enable TLS/HTTPS for all inter-service communication"))
    story.append(bullet("Add rate limiting per user/IP on the orchestrator"))
    story.append(bullet("Implement audit logging for all healthcare data access"))
    story.append(bullet("Add RBAC (Role-Based Access Control) for workflow approval"))
    story.append(bullet("Deploy behind API gateway (Kong, AWS API Gateway)"))
    story.append(bullet("Enable Redis AUTH and encryption at rest"))
    story.append(bullet("Add file type validation and virus scanning on uploads"))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 14 — INTERVIEW TALKING POINTS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("14. Interview Talking Points", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("14.1 Opening Statement (30 seconds)", styles["SubSection"]))
    story.append(Paragraph(
        '<i>"We built a production-grade multi-agent system for healthcare data processing that '
        "uses Google's A2A protocol for agent communication, Anthropic's MCP for tool integration, "
        "and Groq LLM for intelligent planning. The system can read clinical documents, extract "
        "insights, generate summaries, and produce AI-enhanced clinical briefs — all through "
        'specialized agents that discover and coordinate with each other automatically."</i>',
        styles["Callout"]))

    story.append(Paragraph("14.2 Key Selling Points", styles["SubSection"]))
    for item in numbered([
        "<b>Real Protocol Implementation</b>: Not a mock or simulation — we implemented actual A2A agent cards with discovery, actual MCP tool registration with FastMCP, and actual Groq API calls with rate limiting.",
        "<b>Dynamic Planning</b>: The LLM generates execution plans at runtime. Give it a new goal and it figures out which agents and tools to use, in what order, and what can run in parallel.",
        "<b>Production Architecture</b>: Docker Compose orchestrating 7 services with health checks, shared volumes, dependency ordering, and Redis for inter-agent state sharing.",
        "<b>Healthcare Focus</b>: Clinical brief generation, patient data handling with approval gates, and evidence-based analysis — directly relevant to Philips Healthcare.",
        "<b>Cost-Effective</b>: Groq's free tier + open-source stack means zero infrastructure cost for development and demos.",
        "<b>Extensibility</b>: Adding a new agent = create a FastAPI service + agent_card.json. Adding a new tool = add @mcp.tool() decorator. No code changes needed in the orchestrator.",
    ]):
        story.append(item)

    story.append(Paragraph("14.3 Architecture Decisions to Highlight", styles["SubSection"]))
    story.append(make_table(
        ["Decision", "Why It Matters"],
        [
            ["Microservices over monolith",    "Each agent can scale independently. Team can work on agents in parallel. Failure isolation — one agent crashing doesn't take down the system."],
            ["A2A for agent communication",     "Industry standard (Google). Agents are discoverable at runtime. New agents can join without code changes. Interoperable with other A2A systems."],
            ["MCP for tool integration",        "Industry standard (Anthropic). Clean separation between agent logic and tool implementation. Tools are reusable across agents."],
            ["DAG-based execution",             "Allows parallel step execution. Clear dependency tracking. Deterministic ordering. Easy to visualize and debug."],
            ["SSE over WebSockets",             "Simpler, unidirectional (server→client). No connection state management. Native browser support. Perfect for progress streaming."],
            ["Redis over database",             "Ephemeral workflow state doesn't need persistent storage. Sub-ms latency. Automatic TTL cleanup. Lightweight."],
            ["Groq over OpenAI",                "10x faster inference. Free tier for demos. Same model quality (Llama 3.3 70B). Easy to switch if needed."],
        ],
        col_widths=[1.8*inch, 4.4*inch],
    ))

    story.append(PageBreak())

    story.append(Paragraph("14.4 Challenges & How We Solved Them", styles["SubSection"]))
    story.append(make_table(
        ["Challenge", "Solution"],
        [
            ["Async/sync mismatch",
             "Groq SDK is synchronous but agents are async. Wrapped sync calls with asyncio.run_in_executor() to avoid blocking the event loop."],
            ["Context passing between steps",
             "Built a context propagation system where the orchestrator collects outputs from completed dependencies and passes them as context to downstream steps."],
            ["Rate limiting (Groq 429 errors)",
             "Implemented exponential backoff (2s→4s→8s) with automatic fallback to a smaller model (llama-3.1-8b-instant) after 2 failures."],
            ["Model decommissioning",
             "Groq decommissioned llama3-8b-8192. Made model names configurable via environment variables so they can be changed without code changes."],
            ["Docker networking",
             "Services reference each other by container name (e.g., mcp-server:8004). Frontend uses window.location for dynamic API URL detection."],
            ["File sharing across containers",
             "Used a named Docker volume ('uploads') mounted in all services. Files uploaded to one service are immediately accessible to all others."],
        ],
        col_widths=[1.8*inch, 4.4*inch],
    ))

    story.append(Paragraph("14.5 Metrics to Mention", styles["SubSection"]))
    story.append(bullet("<b>7 services</b> running in Docker Compose"))
    story.append(bullet("<b>8 MCP tools</b> registered and discoverable"))
    story.append(bullet("<b>3 specialized agents</b> with A2A protocol"))
    story.append(bullet("<b>51 tests</b> passing (unit + integration)"))
    story.append(bullet("<b>Sub-second planning</b> via Groq (typically 200-500ms)"))
    story.append(bullet("<b>Parallel step execution</b> via DAG engine (asyncio.gather)"))
    story.append(bullet("<b>Real-time streaming</b> via Server-Sent Events"))
    story.append(bullet("<b>Zero infrastructure cost</b> (Groq free tier + Docker)"))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 15 — DEMO WALKTHROUGH
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("15. Demo Walkthrough Script", styles["SectionTitle"]))
    story.append(hr())

    story.append(Paragraph("15.1 Before the Demo", styles["SubSection"]))
    story.append(bullet("Ensure Docker Desktop is running"))
    story.append(bullet("Run <font name='Courier'>docker-compose up -d</font> and verify all 7 services are healthy"))
    story.append(bullet("Open http://localhost:3000 in a browser"))
    story.append(bullet("Have http://localhost:8000/agents open in another tab to show agent discovery"))
    story.append(bullet("Have http://localhost:8000/tools open to show MCP tool registry"))

    story.append(Paragraph("15.2 Demo Script (5 minutes)", styles["SubSection"]))

    story.append(Paragraph("<b>Step 1 — Show the Architecture (1 min)</b>", styles["SubSubSection"]))
    story.append(Paragraph(
        '<i>"This system has 7 Docker containers working together. Let me show you the '
        'discovered agents and available tools..."</i>', styles["Body"]))
    story.append(bullet("Show /agents endpoint → 3 agents with their capabilities"))
    story.append(bullet("Show /tools endpoint → 8 MCP tools with descriptions"))
    story.append(bullet("Point out: \"These are discovered at runtime via A2A and MCP protocols\""))

    story.append(Paragraph("<b>Step 2 — Run a Simple Workflow (2 min)</b>", styles["SubSubSection"]))
    story.append(Paragraph(
        '<i>"Let me show a workflow in action. I\'ll ask the system to read and analyze a '
        'clinical review document..."</i>', styles["Body"]))
    story.append(bullet("Type goal: \"Read and summarize sample_data/clinical_review.txt\""))
    story.append(bullet("Click Execute Workflow"))
    story.append(bullet("Point to Trace Panel: \"Watch the system plan and execute in real-time\""))
    story.append(bullet("Highlight: \"Notice step_2 and step_3 running in parallel — the DAG engine detected they're independent\""))
    story.append(bullet("Show Summary tab: \"Here's the AI-generated clinical brief with key findings and recommendations\""))
    story.append(bullet("Switch to JSON tab: \"And here's the raw data structure for programmatic access\""))

    story.append(Paragraph("<b>Step 3 — Highlight Key Features (1 min)</b>", styles["SubSubSection"]))
    story.append(bullet("Token counter: \"We track every LLM call — input tokens, output tokens, estimated cost\""))
    story.append(bullet("Step badges: \"Each result shows which agent and tool produced it\""))
    story.append(bullet("Clinical brief: \"The AI enhances extractive summaries with clinical implications\""))

    story.append(Paragraph("<b>Step 4 — Technical Deep-Dive (1 min)</b>", styles["SubSubSection"]))
    story.append(Paragraph(
        '<i>"Under the hood, the orchestrator sent this goal to Groq, which generated an execution '
        'plan as a DAG. The reader agent used MCP to read the file, then the analyzer and '
        'summarizer ran in parallel, each calling their own MCP tools. Results flow back through '
        'Redis shared memory and SSE streaming."</i>', styles["Body"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTION 16 — FAQ
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("16. FAQ & Anticipated Questions", styles["SectionTitle"]))
    story.append(hr())

    faqs = [
        ("Why not just use LangChain?",
         "LangChain would abstract away the protocol implementations. Our goal was to demonstrate "
         "understanding of A2A and MCP at the protocol level — how agent discovery, task delegation, "
         "and tool invocation actually work. LangChain is a framework; we built on the standards."),

        ("How would this scale in production?",
         "Each agent is a standalone microservice — scale horizontally with Kubernetes or Docker Swarm. "
         "Redis can be replaced with Redis Cluster. The orchestrator is stateless (state in Redis), "
         "so it can also scale out. Add an API gateway for load balancing."),

        ("What if the Groq API goes down?",
         "The GroqAdapter has retry logic with exponential backoff and model fallback. For production, "
         "we'd add a secondary LLM provider (OpenAI, Anthropic) as a multi-provider fallback chain."),

        ("Why not use a database instead of Redis?",
         "Workflow state is ephemeral (1-hour TTL). We don't need ACID transactions, complex queries, "
         "or persistent storage. Redis gives us sub-millisecond reads and automatic TTL cleanup — "
         "perfect for this use case."),

        ("How do you handle sensitive patient data?",
         "The system supports human-in-the-loop approval gates for sensitive steps. In production, "
         "we'd add HIPAA-compliant encryption, audit logging, access controls, and data anonymization."),

        ("Can you add a new agent without changing the orchestrator?",
         "Yes. Deploy a new FastAPI service with an agent_card.json, add its URL to AGENT_URLS, "
         "and restart the orchestrator. The planner will automatically discover and use it in future plans."),

        ("Why SSE instead of WebSockets?",
         "SSE is unidirectional (server→client), which is all we need for progress updates. "
         "It's simpler to implement, has native browser support, and doesn't require connection "
         "state management. WebSockets would only be needed for bidirectional communication."),

        ("What's the difference between the extractive summary and the clinical brief?",
         "The extractive summary selects the N most important sentences using TF scoring — no LLM needed. "
         "The clinical brief takes that summary plus analysis data and sends it through Groq to produce "
         "a structured, AI-enhanced interpretation with clinical implications and recommendations."),

        ("How does the planner decide what to do?",
         "The planner sends the user's goal, available agents (from A2A cards), and available tools "
         "(from MCP) to Groq with a system prompt that instructs it to generate a minimal DAG. "
         "Groq returns a JSON execution plan with steps, dependencies, and agent assignments."),

        ("What happens if a step fails?",
         "The DAG executor catches exceptions per step. Failed steps are marked in the trace with "
         "error details. Dependent steps will not execute (deadlock detection). The workflow completes "
         "with partial results and error information."),
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>Q: {q}</b>", styles["SubSubSection"]))
        story.append(Paragraph(a, styles["BodyIndent"]))
        story.append(Spacer(1, 0.08*inch))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    #  BACK COVER
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 2*inch))
    story.append(HRFlowable(width="40%", thickness=2, color=ACCENT, spaceAfter=20, spaceBefore=10))
    story.append(Paragraph("Healthcare Multi-Agent Workflow System", styles["CoverSubtitle"]))
    story.append(Paragraph("A2A + MCP + Groq", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "Built with: Python 3.11 · FastAPI · Groq · Redis · Next.js 14 · Docker Compose",
        styles["CoverDate"]))
    story.append(Paragraph(
        "Protocols: Google A2A · Anthropic MCP · Server-Sent Events",
        styles["CoverDate"]))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Document generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                            styles["CoverDate"]))

    # ── Build PDF ────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"\n✅ PDF generated successfully: {OUTPUT_PATH}")
    print(f"   Pages: ~{doc.page}")
    print(f"   Size:  {os.path.getsize(OUTPUT_PATH) / 1024:.0f} KB")


if __name__ == "__main__":
    build()
