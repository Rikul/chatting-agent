"""Chat manager for handling conversation state and logic."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple


@dataclass
class Message:
    """Represents a single message in the conversation."""
    agent_name: str  # "Agent 1" or "Agent 2" for display
    content: str
    timestamp: datetime

    def get_streamlit_role(self) -> str:
        """
        Get the Streamlit-compatible role for st.chat_message().

        Streamlit only accepts 'user' or 'assistant' as valid roles.
        Agent 1 -> 'user', Agent 2 -> 'assistant'
        """
        return "user" if self.agent_name == "Agent 1" else "assistant"

    def get_avatar(self) -> str:
        """Get an emoji avatar for the agent."""
        return "🤖" if self.agent_name == "Agent 1" else "🦾"

    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format."""
        return {
            "agent_name": self.agent_name,
            "content": self.content,
            "timestamp": self.timestamp.strftime("%H:%M:%S")
        }


@dataclass
class ConversationState:
    """Manages the state of a conversation between two agents."""
    agent1_model: str
    agent2_model: str
    topic: str
    turn_limit_minutes: int
    system_prompt: str = ""
    messages: List[Message] = field(default_factory=list)
    is_running: bool = False
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    current_agent: int = 1  # 1 or 2

    def get_agent_model(self, agent_number: int) -> str:
        """Get the model name for the specified agent number."""
        return self.agent1_model if agent_number == 1 else self.agent2_model
    
    def start_conversation(self) -> None:
        """Start the conversation with the initial topic message."""
        self.is_running = True
        self.start_time = datetime.now()
        self.finish_time = None
        self.current_agent = 1
        self.messages = [
            Message(
                agent_name=self.get_agent_model(self.current_agent),
                content=self.topic,
                timestamp=datetime.now()
            )
        ]

    def stop_conversation(self) -> None:
        """Stop the conversation."""
        self.is_running = False
        self.finish_time = datetime.now()

    def add_message(self, content: str) -> None:
        """Add a message from the current agent."""
        agent_name = f"Agent {self.current_agent}"
        message = Message(
            agent_name=self.get_agent_model(self.current_agent),
            content=content,
            timestamp=datetime.now()
        )
        self.messages.append(message)

    def switch_agent(self) -> None:
        """Switch to the other agent."""
        self.current_agent = 2 if self.current_agent == 1 else 1

    def get_current_agent_info(self) -> Tuple[str, str]:
        """
        Get the current agent's name and model.

        Returns:
            Tuple of (agent_name, model_name)
        """
        if self.current_agent == 1:
            return "Agent 1", self.agent1_model
        else:
            return "Agent 2", self.agent2_model

    def get_next_agent_info(self) -> Tuple[str, str]:
        """
        Get the next agent's name and model (without switching).

        Returns:
            Tuple of (agent_name, model_name)
        """
        if self.current_agent == 1:
            return "Agent 2", self.agent2_model
        else:
            return "Agent 1", self.agent1_model

    def is_time_limit_reached(self) -> bool:
        """Check if the time limit has been reached."""
        if self.turn_limit_minutes == 0:
            return False
        if not self.start_time:
            return False
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        return elapsed_seconds > self.turn_limit_minutes * 60

    def get_elapsed_time_str(self) -> str:
        """Get the elapsed time as a formatted string."""
        if not self.start_time:
            return "Not started"
        if self.finish_time:
            elapsed = self.finish_time - self.start_time
        else:
            elapsed = datetime.now() - self.start_time

        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        return f"{minutes}m {seconds}s"

    def get_duration_str(self) -> str:
        """Get the total duration as a formatted string."""
        if not self.start_time:
            return "Not started"
        if not self.finish_time:
            return "In progress"

        elapsed = self.finish_time - self.start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        return f"{minutes}m {seconds}s"

    def export_to_markdown(self) -> str:
        """Export the conversation to markdown format."""
        start_time_str = (
            self.start_time.strftime('%Y-%m-%d %H:%M:%S')
            if self.start_time else "Not started"
        )
        finish_time_str = (
            self.finish_time.strftime('%Y-%m-%d %H:%M:%S')
            if self.finish_time else "Not finished"
        )

        markdown = f"""# Chat on Topic: {self.topic}

**Start Time:** {start_time_str}
**Finish Time:** {finish_time_str}
**Duration:** {self.get_duration_str()}

**Agent 1 Model:** {self.agent1_model}
**Agent 2 Model:** {self.agent2_model}
**Turn Limit:** {self.turn_limit_minutes} minutes {"(unlimited)" if self.turn_limit_minutes == 0 else ""}
**System Prompt:** {self.system_prompt}

---

"""
        for message in self.messages:
            timestamp = message.timestamp.strftime("%H:%M:%S")
            markdown += f"**{message.agent_name}** ({timestamp})\n{message.content}\n\n"

        return markdown

    def get_messages_for_model(self) -> List[Dict[str, str]]:
        """Get messages in the format expected by the model."""
        return [{"role": m.agent_name, "content": m.content} for m in self.messages]
