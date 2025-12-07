# Agents Architecture

This document describes the agent architecture used in the Chatting Agents application.

## Overview

The Chatting Agents application creates autonomous conversations between two independently running Ollama language models. Each model acts as an "agent" with its own identity and model backend.

## Agent Structure

### Agent Definition

Agents are not explicitly defined as classes but are represented through:

- **Agent Identity**: Each agent is identified as "Agent 1" or "Agent 2"
- **Model Backend**: Each agent uses a specific Ollama model (e.g., llama2, mistral)
- **System Prompt**: Both agents share a common system prompt that guides their behavior

### Agent State Management

Agents are managed through the `ConversationState` class (`chat_manager.py`):

```python
@dataclass
class ConversationState:
    agent1_model: str          # Model for Agent 1
    agent2_model: str          # Model for Agent 2
    topic: str                 # Conversation topic
    turn_limit_minutes: int    # Time limit for conversation
    system_prompt: str         # Shared instructions for both agents
    messages: List[Message]    # Conversation history
    current_agent: int         # Currently active agent (1 or 2)
```

## Agent Behavior

### System Prompt

Both agents follow the same system prompt (configurable via `SYSTEM_PROMPT` environment variable):

```
Engage in thoughtful, productive discussions. Share insights, consider different perspectives,
and build upon each other's ideas. Keep responses concise and focused on the topic.
```

This creates a cooperative conversation style where agents:
- Build upon each other's ideas
- Consider multiple perspectives
- Stay focused on the topic
- Keep responses concise

### Turn Management

The conversation follows a strict turn-based system:

1. **Initialization**: Agent 1 starts with the initial topic message
2. **Turn Switching**: After each response, the system switches to the other agent
3. **Role Assignment**: 
   - Agent 1 uses "user" role in Streamlit UI (🤖 avatar)
   - Agent 2 uses "assistant" role in Streamlit UI (🦾 avatar)

### Message Flow

```
User Input (Topic) → Agent 1 Model → Response → 
→ Agent 2 Model → Response → Agent 1 Model → ...
```

Each agent receives:
- All previous messages in the conversation history
- The shared system prompt
- Their specific model's context and capabilities

## Agent Communication

### Message Format

Messages between agents are stored as:

```python
@dataclass
class Message:
    agent_name: str      # Display name (model name)
    content: str         # Message content
    timestamp: datetime  # When the message was created
```

### Context Passing

When an agent generates a response:
1. All previous messages are converted to model format
2. Last message is marked as "user" role (the prompt to respond to)
3. All previous messages are marked as "assistant" role (conversation history)
4. System prompt is included to maintain behavior

## Agent Constraints

### Time Limits

Conversations can have optional time limits:
- **0 minutes**: Unlimited conversation
- **N minutes**: Stops automatically after N minutes

### Validation Rules

- Agents must use different models (same model for both is disallowed)
- Topic must be non-empty
- At least one Ollama model must be available

### Error Handling

Agents handle errors gracefully:
- Empty responses stop the conversation with an error message
- Connection errors to Ollama are caught and displayed
- Streaming failures are logged and conversation stops

## Agent Independence

Each agent operates independently:

- **Separate Models**: Each agent uses its own Ollama model instance
- **No Shared Memory**: Agents only share conversation history, not internal state
- **Autonomous Responses**: Each agent generates responses based on its model's capabilities
- **No Coordination**: Agents don't coordinate or plan responses together

## Customization

### Changing Agent Behavior

Modify the system prompt via environment variable:

```bash
export SYSTEM_PROMPT="You are a debate expert. Challenge ideas and defend your positions."
```

Or in the UI, edit the "System Prompt" field before starting the conversation.

### Model Selection

Choose from any locally available Ollama models:
```bash
ollama pull llama2
ollama pull mistral
ollama pull codellama
```

Different model combinations create different conversation dynamics:
- **Similar models**: More agreement, similar reasoning
- **Different models**: More diverse perspectives, varied approaches

## Technical Implementation

### Agent Generation

Response generation happens in `ollama_client.py`:

```python
def generate_response(model, messages, system_prompt) -> Iterator[str]:
    # Converts agent messages to model format
    # Streams response token by token
    # Returns chunks for real-time display
```

### Agent Switching

Turn management in `chat_manager.py`:

```python
def switch_agent(self) -> None:
    """Switch to the other agent."""
    self.current_agent = 2 if self.current_agent == 1 else 1
```

### Conversation Loop

The main loop in `app.py`:

1. Check if time limit reached
2. Get next agent info
3. Display agent's response with streaming
4. Add message to conversation history
5. Switch to other agent
6. Trigger rerun to continue conversation

## Future Enhancements

Potential improvements to the agent system:

- **Multiple Agents**: Support for 3+ agents in conversation
- **Agent Personas**: Different system prompts per agent
- **Agent Memory**: Persistent memory across conversations
- **Agent Tools**: Give agents access to external tools/APIs
- **Agent Interruption**: Allow manual interjection during conversation
- **Agent Voting**: Multiple agents vote on a topic
- **Agent Specialization**: Agents with different domains of expertise
