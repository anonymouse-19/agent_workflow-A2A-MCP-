"""
Base Agent — Abstract base class for all agents in the system.

Every agent:
  - Has a name and a list of capabilities
  - Communicates via the MessageBus (A2A)
  - Accesses tools via the ToolRegistry (MCP)
  - Implements process() to handle incoming messages
"""

from ..core.message_bus import MessageBus
from ..core.models import Message, MessageType
from ..tools.registry import ToolRegistry


class BaseAgent:
    """
    Abstract base for all agents.
    Subclasses must implement process(message) → dict.
    """

    def __init__(self, name: str, capabilities: list, bus: MessageBus, tools: ToolRegistry):
        self.name = name
        self.capabilities = capabilities
        self.bus = bus
        self.tools = tools
        bus.register_agent(name, self)

    def send(self, recipient: str, payload: dict,
             msg_type: MessageType = MessageType.REQUEST,
             correlation_id: str = ""):
        """Send a message to another agent via the bus."""
        msg = Message(
            sender=self.name,
            recipient=recipient,
            msg_type=msg_type,
            payload=payload,
            correlation_id=correlation_id,
        )
        self.bus.send(msg)
        return msg

    def receive(self):
        """Receive the next message from this agent's queue."""
        return self.bus.receive(self.name)

    def request(self, recipient: str, payload: dict) -> dict:
        """
        True A2A peer-to-peer communication: send a request to another
        agent through the MessageBus and receive the response.
        No direct method calls — all communication flows through the bus.
        """
        self.send(recipient, payload)
        response = self.bus.dispatch(recipient)
        if response:
            return response.payload
        return {"error": f"No response from {recipient}"}

    def select_tool(self, task_hint: str):
        """
        MCP-style tool selection: dynamically pick a tool based on context.
        The agent inspects the registry and chooses — not hardcoded.
        """
        matches = self.tools.find_for_task([task_hint])
        if matches:
            return matches[0]["name"]
        return None

    def process(self, message: Message) -> dict:
        """Process an incoming message. Must be implemented by subclasses."""
        raise NotImplementedError(f"{self.name} must implement process()")

    def __repr__(self):
        return f"Agent({self.name}, capabilities={self.capabilities})"
