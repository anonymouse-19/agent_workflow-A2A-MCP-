"""
Shared Pydantic models for the Agent Workflow System.

Defines: A2A Task, Step, ExecutionPlan, AgentCard, TraceEvent, TokenUsage.
"""

from __future__ import annotations

import uuid
import time
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── A2A Task Status ──────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires-approval"


# ── A2A Task Object ──────────────────────────────────────────────────────────

class A2ATask(BaseModel):
    """A2A task object sent between orchestrator and agents."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: Optional[str] = None
    tool: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


# ── Execution Plan Step ──────────────────────────────────────────────────────

class PlanStep(BaseModel):
    """A single step in the LLM-generated execution plan DAG."""
    step_id: str
    agent: str
    tool: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    requires_approval: bool = False


class ExecutionPlan(BaseModel):
    """LLM-generated DAG execution plan."""
    steps: List[PlanStep]


# ── Agent Card (A2A Discovery) ───────────────────────────────────────────────

class AgentCapability(BaseModel):
    """Describes a single capability of an agent."""
    name: str
    description: str = ""


class AgentCard(BaseModel):
    """A2A Agent Card — exposed at GET /.well-known/agent.json"""
    name: str
    url: str
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    inputModes: List[str] = Field(default_factory=lambda: ["application/json"])
    outputModes: List[str] = Field(default_factory=lambda: ["application/json"])


# ── SSE Trace Event ──────────────────────────────────────────────────────────

class TraceEvent(BaseModel):
    """A single event streamed to the frontend via SSE."""
    timestamp: float = Field(default_factory=time.time)
    agent: str
    tool: Optional[str] = None
    status: str
    detail: str
    step_id: Optional[str] = None
    correlation_id: Optional[str] = None
    groq_model: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None


# ── Token Usage Tracking ─────────────────────────────────────────────────────

class TokenUsage(BaseModel):
    """Tracks Groq API token usage across the workflow."""
    model_config = {"protected_namespaces": ()}

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_calls: int = 0
    model_usage: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    def add(self, model: str, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_calls += 1
        if model not in self.model_usage:
            self.model_usage[model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        self.model_usage[model]["input_tokens"] += input_tokens
        self.model_usage[model]["output_tokens"] += output_tokens
        self.model_usage[model]["calls"] += 1

    @property
    def estimated_cost_usd(self) -> float:
        """Estimate cost based on Groq pricing (approximate)."""
        # Groq pricing: ~$0.05/1M input tokens, ~$0.08/1M output tokens for llama-3.3-70b
        cost = (self.total_input_tokens * 0.05 / 1_000_000) + \
               (self.total_output_tokens * 0.08 / 1_000_000)
        return round(cost, 6)


# ── Workflow Run Request ─────────────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    """Request to start a new workflow run."""
    goal: str
    files: List[str] = Field(default_factory=list)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class StepApproval(BaseModel):
    """Human-in-the-loop approval for a step."""
    step_id: str
    approved: bool
    correlation_id: str
