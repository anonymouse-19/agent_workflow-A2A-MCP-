"""
A2A Message Bus — Central communication hub for agent-to-agent messaging.

This is the backbone of the A2A protocol implementation.
Agents never call each other directly; all communication flows through
the MessageBus as discrete Message objects.
"""

from collections import defaultdict, deque
from typing import Optional, List

from .models import Message, MessageType


class MessageBus:
    """
    Routes messages between agents. Each agent has its own queue.
    
    Design:
      - Agents register themselves on the bus.
      - send() enqueues a message for the recipient.
      - receive() dequeues the next message for an agent.
      - All messages are logged for observability.
    """

    def __init__(self):
        self._queues: dict = defaultdict(deque)
        self._message_log: List[Message] = []
        self._registered_agents: set = set()
        self._agents: dict = {}  # name → agent instance (for A2A dispatch)

    def register_agent(self, agent_name: str, agent_instance=None):
        """Register an agent so it can send/receive messages."""
        self._registered_agents.add(agent_name)
        self._registered_agents.add("orchestrator")
        if agent_instance is not None:
            self._agents[agent_name] = agent_instance

    def dispatch(self, recipient: str):
        """
        A2A dispatch: deliver the next queued message to the recipient,
        let the agent process it, and return the response Message.
        Both request and response are logged for observability.
        """
        agent = self._agents.get(recipient)
        if not agent:
            return None
        msg = self.receive(recipient)
        if not msg:
            return None
        result = agent.process(msg)
        response = Message(
            sender=recipient,
            recipient=msg.sender,
            msg_type=MessageType.RESPONSE,
            payload=result if isinstance(result, dict) else {"result": result},
            correlation_id=msg.correlation_id,
        )
        self._message_log.append(response)
        return response

    def send(self, message: Message):
        """Send a message to a specific agent's queue."""
        self._queues[message.recipient].append(message)
        self._message_log.append(message)

    def receive(self, agent_name: str) -> Optional[Message]:
        """Receive the next message from an agent's queue (FIFO)."""
        if self._queues[agent_name]:
            return self._queues[agent_name].popleft()
        return None

    def has_messages(self, agent_name: str) -> bool:
        """Check if an agent has pending messages."""
        return bool(self._queues[agent_name])

    def get_log(self) -> List[Message]:
        """Return all messages sent through the bus (for debugging)."""
        return list(self._message_log)

    def message_count(self) -> int:
        """Total number of messages ever sent."""
        return len(self._message_log)
