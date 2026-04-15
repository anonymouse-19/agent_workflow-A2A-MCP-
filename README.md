# Healthcare Multi-Agent Workflow — A2A + MCP + Groq

Production-grade multi-agent system for **healthcare data processing** using:
- **A2A (Agent-to-Agent)** protocol — Google's open standard for agent communication
- **MCP (Model Context Protocol)** — Anthropic's tool integration standard via `mcp` Python SDK
- **Groq** — only LLM backend (llama-3.3-70b-versatile)
- **FastAPI** microservices, **Redis** shared memory, **Next.js 14** streaming UI

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)          :3000                           │
│  ┌─────────────────┐  ┌──────────────────┐                     │
│  │ Execution Trace  │  │ Output (Markdown) │   SSE streaming    │
│  │ (left panel)     │  │ (right panel)     │                    │
│  └─────────────────┘  └──────────────────┘                     │
└───────────────┬─────────────────────────────────────────────────┘
                │ POST /workflow/stream
┌───────────────▼─────────────────────────────────────────────────┐
│  Orchestrator (FastAPI)         :8000                            │
│  ┌──────────────┐  ┌──────────┐  ┌───────────┐                 │
│  │ AgentRegistry│  │ Planner  │  │ DAG Engine│                  │
│  │ (discover)   │  │ (Groq)   │  │ (parallel)│                  │
│  └──────────────┘  └──────────┘  └───────────┘                  │
└────┬──────────┬──────────┬──────────────────────────────────────┘
     │ A2A      │ A2A      │ A2A
┌────▼────┐ ┌───▼─────┐ ┌─▼──────────┐   ┌─────────────────────┐
│ Reader  │ │Analyzer │ │Summarizer  │   │  MCP Server  :8004  │
│  :8001  │ │  :8002  │ │   :8003    │   │  (FastMCP + 8 tools)│
└────┬────┘ └───┬─────┘ └─┬──────────┘   └─────────┬───────────┘
     │ MCP      │ MCP      │ MCP                    │
     └──────────┴──────────┴────────────────────────┘
                                    │
                              ┌─────▼──────┐
                              │   Redis    │
                              │  (shared)  │
                              └────────────┘
```

---

## Folder Structure

```
philips_3.1/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── shared/
│   ├── models.py              # Pydantic models (A2ATask, PlanStep, etc.)
│   ├── llm_adapter.py         # Groq-only LLM wrapper with retry
│   └── redis_store.py         # Async Redis shared memory
├── mcp_server/
│   └── server.py              # FastMCP server with 8 @mcp.tool() tools
├── agents/
│   ├── reader/
│   │   ├── main.py            # FastAPI microservice :8001
│   │   └── agent_card.json    # A2A Agent Card
│   ├── analyzer/
│   │   ├── main.py            # FastAPI microservice :8002
│   │   └── agent_card.json
│   └── summarizer/
│       ├── main.py            # FastAPI microservice :8003
│       └── agent_card.json
├── orchestrator/
│   ├── main.py                # FastAPI orchestrator :8000
│   ├── planner.py             # Groq-powered dynamic planner
│   └── agent_registry.py     # A2A agent discovery
├── frontend/
│   ├── app/page.tsx           # Next.js 14 SSE streaming UI
│   ├── package.json
│   └── Dockerfile
├── tests/
│   ├── test_groq_adapter.py
│   ├── test_mcp_server.py
│   ├── test_agent_cards.py
│   ├── test_planner.py
│   └── test_orchestrator.py
└── sample_data/
    ├── sample.txt
    └── create_samples.py
```

---

## Quick Start (Local)

### 1. Set up environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate sample data (optional)

```bash
python sample_data/create_samples.py
```

### 4. Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 5. Start all services (5 terminals)

```bash
# Terminal 1: MCP Server
python -m mcp_server.server

# Terminal 2: Reader Agent
python -m agents.reader.main

# Terminal 3: Analyzer Agent
python -m agents.analyzer.main

# Terminal 4: Summarizer Agent
python -m agents.summarizer.main

# Terminal 5: Orchestrator
python -m orchestrator.main
```

### 6. Start frontend

```bash
cd frontend && npm install && npm run dev
```

Open http://localhost:3000

---

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY

docker-compose up --build
```

Services: Orchestrator :8000 | Reader :8001 | Analyzer :8002 | Summarizer :8003 | MCP :8004 | Frontend :3000

---

## API Usage

### Start a workflow

```bash
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{"goal": "Read sample.txt, extract questions, and produce a clinical brief", "files": ["sample_data/sample.txt"]}'
```

### Stream a workflow (SSE)

```bash
curl -N -X POST http://localhost:8000/workflow/stream \
  -H "Content-Type: application/json" \
  -d '{"goal": "Summarize and analyze sample.txt", "files": ["sample_data/sample.txt"]}'
```

### List discovered agents

```bash
curl http://localhost:8000/agents
```

### List MCP tools

```bash
curl http://localhost:8000/tools
```

---

## Running Tests

```bash
# Unit tests (no API key needed)
python -m pytest tests/ -v -k "not live"

# Integration tests (requires GROQ_API_KEY)
GROQ_API_KEY=gsk_... python -m pytest tests/ -v
```

---

## Key Protocols

### A2A (Agent-to-Agent)
- Each agent exposes `GET /.well-known/agent.json` (Agent Card)
- Tasks sent via `POST /tasks/send` with `{id, correlation_id, input}`
- Streaming via `POST /tasks/stream` (Server-Sent Events)

### MCP (Model Context Protocol)
- MCP server built with `FastMCP` from the official `mcp` Python SDK
- 8 tools registered with `@mcp.tool()` decorator
- Agents connect as MCP clients using `streamable_http_client`
- Tools: `read_pdf`, `read_excel`, `read_text`, `extract_questions`, `summarize_text`, `extract_keywords`, `analyze_tabular_data`, `llm_enhance`

### Groq LLM
- Default model: `llama-3.3-70b-versatile`
- Fallback: `llama-3.1-8b-instant`
- Retry with exponential backoff on rate limits
- Token tracking across all agents
