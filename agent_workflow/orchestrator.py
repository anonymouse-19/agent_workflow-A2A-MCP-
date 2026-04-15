"""
Orchestrator — Executes dynamically-generated plans via A2A messaging.

The Orchestrator is NOT an agent itself; it's the runtime engine that:
  1. Sends the task to the PlannerAgent (via A2A message)
  2. Receives the execution plan
  3. Iterates through plan steps, routing messages to the right agents
  4. Passes context between steps (shared state)
  5. Adapts when steps fail (skips failed steps, continues with rest)
  6. Collects and returns final results

All agent interactions go through the MessageBus — the Orchestrator
never calls agent internals directly.
"""

from .core.message_bus import MessageBus
from .core.models import Message, MessageType, ExecutionPlan, ExecutionTrace


class Orchestrator:

    def __init__(self, bus: MessageBus, agents: dict, trace: ExecutionTrace):
        self.bus = bus
        self.agents = agents   # name → agent instance
        self.trace = trace

    def execute(self, task: str, files: list) -> dict:
        """Execute a task end-to-end: plan → route → collect results."""

        self.trace.log("orchestrator", "TASK_RECEIVED", f"Task: {task}")
        self.trace.log("orchestrator", "FILES", f"Input files: {', '.join(files)}")

        # ── Step 1: Ask Planner to generate an execution plan ────────────
        planner = self.agents["planner"]
        plan_msg = Message(
            sender="orchestrator",
            recipient="planner",
            msg_type=MessageType.REQUEST,
            payload={"task": task, "files": files},
        )

        self.trace.log("planner", "PLANNING", f"Analyzing task to create execution plan")
        plan_result = planner.process(plan_msg)
        plan: ExecutionPlan = plan_result["plan"]

        # Display the generated plan
        step_summary = " → ".join(f"{s.action}@{s.agent}" for s in plan.steps)
        self.trace.log("planner", "PLAN_READY", f"{len(plan.steps)} steps: {step_summary}")
        plan.display()

        # ── Step 2: Execute plan step-by-step ────────────────────────────
        context = {}       # shared data between steps (accumulated results)
        all_results = {}   # final results keyed by action

        while not plan.is_complete():
            step = plan.next_step()
            if step is None:
                # No more executable steps (remaining have unmet deps)
                self.trace.log("orchestrator", "BLOCKED", "No executable steps remain")
                break

            step.status = "running"
            agent = self.agents.get(step.agent)

            if not agent:
                step.status = "failed"
                step.result = {"error": f"Agent '{step.agent}' not registered"}
                self.trace.log("orchestrator", "AGENT_MISSING", f"'{step.agent}' not found")
                continue

            # Build message payload with shared context
            payload = {**step.params, "context": context}

            # For summarizer: include analysis results from earlier steps
            if step.agent == "summarizer":
                analysis = {}
                for prev in plan.steps:
                    if prev.status == "completed" and prev.action in (
                        "analyze_data", "extract_questions", "extract_keywords"
                    ):
                        analysis[prev.action] = prev.result
                payload["analysis"] = analysis

            # A2A: Send message to agent
            msg = Message(
                sender="orchestrator",
                recipient=step.agent,
                msg_type=MessageType.REQUEST,
                payload=payload,
            )

            self.trace.log(
                step.agent, f"EXEC:{step.action}",
                f"Step {step.step_id} — processing",
            )

            try:
                # A2A: Agent processes the message and returns result
                result = agent.process(msg)

                if isinstance(result, dict) and "error" in result:
                    step.status = "failed"
                    step.result = result
                    self.trace.log(step.agent, "FAILED", str(result["error"])[:80])
                    # Adaptation: continue with remaining steps
                    self.trace.log(
                        "orchestrator", "ADAPTING",
                        f"Step {step.step_id} failed — skipping, continuing plan",
                    )
                else:
                    step.status = "completed"
                    step.result = result

                    # Update shared context for downstream steps
                    if step.action == "read_file":
                        file_key = step.params.get("file_path", f"step_{step.step_id}")
                        context[file_key] = result

                    detail = self._summarize_result(result)
                    self.trace.log(step.agent, "DONE", detail)
                    all_results[step.action] = result

            except Exception as e:
                step.status = "failed"
                step.result = {"error": str(e)}
                self.trace.log(step.agent, "EXCEPTION", str(e)[:80])

        # ── Step 3: Compile final output ─────────────────────────────────
        plan.status = "completed"
        completed = sum(1 for s in plan.steps if s.status == "completed")
        failed = sum(1 for s in plan.steps if s.status == "failed")
        self.trace.log(
            "orchestrator", "FINISHED",
            f"{completed}/{len(plan.steps)} steps completed, {failed} failed",
        )

        return all_results

    def _summarize_result(self, result) -> str:
        """Create a brief summary of a step result for the trace log."""
        if not isinstance(result, dict):
            return str(result)[:80]
        if "content" in result:
            return f"Read {result.get('chars', len(result['content']))} chars"
        if "summary" in result:
            return f"Summary ({result.get('method', '?')}): {result['summary'][:60]}..."
        if "questions" in result:
            return f"Found {result.get('count', len(result['questions']))} questions"
        if "keywords" in result:
            kws = result["keywords"][:5]
            return f"Keywords: {', '.join(kws)}"
        if "insights" in result:
            return f"{len(result['insights'])} insights generated"
        if "sheets" in result:
            names = result.get("sheet_names", [])
            return f"Read Excel with sheets: {', '.join(names)}"
        return str(result)[:80]
