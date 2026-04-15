"""
Core data models for the agent workflow system.
Defines Message, Step, ExecutionPlan, and ExecutionTrace.
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class MessageType(Enum):
    """Types of messages exchanged between agents (A2A protocol)."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class Message:
    """
    A2A Message — the fundamental unit of inter-agent communication.
    Every interaction between agents happens through Message objects
    routed via the MessageBus.
    """
    sender: str
    recipient: str
    msg_type: MessageType
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return (
            f"Message(id={self.message_id[:8]}.. "
            f"{self.sender}→{self.recipient} "
            f"type={self.msg_type.value})"
        )


@dataclass
class Step:
    """A single step in a dynamically generated execution plan."""
    step_id: int
    action: str       # e.g. "read_file", "extract_questions", "summarize"
    agent: str        # which agent handles this step
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[int] = field(default_factory=list)
    status: str = "pending"   # pending | running | completed | failed
    result: Any = None

    def __repr__(self):
        deps = f" (after {self.depends_on})" if self.depends_on else ""
        return f"Step({self.step_id}: {self.action}@{self.agent} [{self.status}]{deps})"


@dataclass
class ExecutionPlan:
    """
    A runtime-generated plan that determines the sequence of agent actions.
    Created by the PlannerAgent — NOT hardcoded.
    """
    task_description: str
    steps: List[Step] = field(default_factory=list)
    status: str = "pending"

    def next_step(self) -> Optional[Step]:
        """Get the next executable step (all dependencies satisfied)."""
        for step in self.steps:
            if step.status == "pending":
                deps_met = all(
                    self.steps[d].status == "completed"
                    for d in step.depends_on
                    if d < len(self.steps)
                )
                if deps_met:
                    return step
        return None

    def is_complete(self) -> bool:
        return all(s.status in ("completed", "failed") for s in self.steps)

    def display(self):
        print(f"\n  Execution Plan: {self.task_description}")
        print(f"  {'─' * 50}")
        for step in self.steps:
            deps = f" (after steps {step.depends_on})" if step.depends_on else ""
            print(f"    Step {step.step_id}: {step.action} → agent:{step.agent}{deps}")


@dataclass
class TraceEntry:
    """A single entry in the execution trace log."""
    timestamp: float
    agent: str
    action: str
    detail: str


class ExecutionTrace:
    """Records every action taken during execution for full observability."""

    def __init__(self):
        self.entries: List[TraceEntry] = []
        self._start_time: float = time.time()

    def log(self, agent: str, action: str, detail: str):
        entry = TraceEntry(time.time(), agent, action, detail)
        self.entries.append(entry)
        elapsed = entry.timestamp - self._start_time
        print(f"  [{elapsed:6.3f}s] {agent:>12} │ {action:<20} │ {detail[:80]}")

    def display(self):
        print(f"\n{'═' * 78}")
        print(f"  EXECUTION TRACE  ({len(self.entries)} actions)")
        print(f"{'═' * 78}")
        for i, entry in enumerate(self.entries, 1):
            elapsed = entry.timestamp - self._start_time
            print(f"  {i:3}. [{elapsed:6.3f}s] {entry.agent:>12} │ {entry.action:<20} │ {entry.detail[:60]}")
        print(f"{'═' * 78}")
