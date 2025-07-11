"""
Base Agent Class for WatchTower AI Multi-Agent System
File: backend/agents/base_agent.py
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json

# Set up logging
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in the system"""
    HEALTH = "health"
    ANALYSIS = "analysis"
    QUERY = "query"
    DASHBOARD = "dashboard"
    ORCHESTRATOR = "orchestrator"


class MessageType(Enum):
    """Types of messages between agents"""
    QUERY = "query"
    RESPONSE = "response"
    ALERT = "alert"
    INSIGHT = "insight"
    ACTION = "action"
    STATUS = "status"


@dataclass
class AgentMessage:
    """Message structure for agent communication"""
    id: str
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "context": self.context
        }


class BaseAgent(ABC):
    """Base class for all WatchTower AI agents"""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.is_running = False
        self.message_queue = asyncio.Queue()
        self.subscribers: List[Callable] = []
        self.context_memory: Dict[str, Any] = {}

        # Performance tracking
        self.messages_processed = 0
        self.start_time = datetime.now()
        self.last_activity = datetime.now()

        logger.info(f"Initialized {agent_type.value} agent: {agent_id}")

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message and return response if needed"""
        pass

    @abstractmethod
    async def background_task(self):
        """Background task that runs continuously"""
        pass

    async def start(self):
        """Start the agent"""
        if self.is_running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return

        self.is_running = True
        logger.info(f"Starting agent: {self.agent_id}")

        # Start message processing and background tasks as separate tasks
        asyncio.create_task(self._message_processor())
        asyncio.create_task(self._background_task_wrapper())

        # Agent is now started (tasks run in background)
        logger.info(f"Agent {self.agent_id} started successfully")

    async def stop(self):
        """Stop the agent"""
        self.is_running = False
        logger.info(f"Stopping agent: {self.agent_id}")

    async def send_message(self, message: AgentMessage):
        """Send message to subscribers"""
        self.last_activity = datetime.now()

        # Notify all subscribers
        for subscriber in self.subscribers:
            try:
                await subscriber(message)
            except Exception as e:
                logger.error(f"Error sending message to subscriber: {e}")

    async def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        await self.message_queue.put(message)

    def subscribe(self, callback: Callable):
        """Subscribe to messages from this agent"""
        self.subscribers.append(callback)

    def unsubscribe(self, callback: Callable):
        """Unsubscribe from messages"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def _message_processor(self):
        """Process incoming messages"""
        while self.is_running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                # Process the message
                response = await self.process_message(message)
                self.messages_processed += 1
                self.last_activity = datetime.now()

                # Send response if generated
                if response:
                    await self.send_message(response)

            except asyncio.TimeoutError:
                # No message received, continue
                continue
            except Exception as e:
                logger.error(
                    f"Error processing message in {self.agent_id}: {e}")

    async def _background_task_wrapper(self):
        """Wrapper for background task with error handling"""
        while self.is_running:
            try:
                await self.background_task()
                await asyncio.sleep(1)  # Prevent tight loop
            except Exception as e:
                logger.error(
                    f"Error in background task for {self.agent_id}: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def update_context(self, key: str, value: Any):
        """Update agent context memory"""
        self.context_memory[key] = value

    def get_context(self, key: str) -> Any:
        """Get value from agent context memory"""
        return self.context_memory.get(key)

    def clear_context(self):
        """Clear agent context memory"""
        self.context_memory.clear()

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        uptime = datetime.now() - self.start_time
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "is_running": self.is_running,
            "messages_processed": self.messages_processed,
            "uptime_seconds": uptime.total_seconds(),
            "last_activity": self.last_activity.isoformat(),
            "queue_size": self.message_queue.qsize(),
            "subscribers": len(self.subscribers),
            "context_items": len(self.context_memory)
        }

    def log_info(self, message: str):
        """Log info message with agent context"""
        logger.info(f"[{self.agent_id}] {message}")

    def log_warning(self, message: str):
        """Log warning message with agent context"""
        logger.warning(f"[{self.agent_id}] {message}")

    def log_error(self, message: str):
        """Log error message with agent context"""
        logger.error(f"[{self.agent_id}] {message}")


class AgentCommunicationHub:
    """Central hub for agent communication"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history = 1000

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the hub"""
        self.agents[agent.agent_id] = agent

        # Subscribe to agent messages
        agent.subscribe(self._handle_message)

        logger.info(f"Registered agent: {agent.agent_id}")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")

    async def _handle_message(self, message: AgentMessage):
        """Handle message routing between agents"""
        # Store in history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

        # Route to recipient
        if message.recipient == "broadcast":
            # Broadcast to all agents except sender
            for agent_id, agent in self.agents.items():
                if agent_id != message.sender:
                    await agent.receive_message(message)
        elif message.recipient in self.agents:
            # Direct message to specific agent
            await self.agents[message.recipient].receive_message(message)
        else:
            logger.warning(f"Message recipient not found: {message.recipient}")

    async def send_message(self, message: AgentMessage):
        """Send message through the hub"""
        await self._handle_message(message)

    def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }

    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return [
            message.to_dict()
            for message in self.message_history[-limit:]
        ]

    async def start_all_agents(self):
        """Start all registered agents"""
        tasks = []
        for agent in self.agents.values():
            tasks.append(agent.start())

        logger.info(f"Starting {len(tasks)} agents...")
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all_agents(self):
        """Stop all registered agents"""
        for agent in self.agents.values():
            await agent.stop()

        logger.info("All agents stopped")


# Global communication hub instance
communication_hub = AgentCommunicationHub()


def create_message(
    sender: str,
    recipient: str,
    message_type: MessageType,
    content: Dict[str, Any],
    priority: int = 1,
    context: Optional[Dict[str, Any]] = None
) -> AgentMessage:
    """Utility function to create agent messages"""
    import uuid

    return AgentMessage(
        id=str(uuid.uuid4()),
        sender=sender,
        recipient=recipient,
        message_type=message_type,
        content=content,
        timestamp=datetime.now(),
        priority=priority,
        context=context
    )
