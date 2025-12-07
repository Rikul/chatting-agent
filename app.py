"""Auto-pilot Chatting Agents - A Streamlit app for AI agent conversations."""
import streamlit as st
from datetime import datetime
import logging
from typing import Optional
import time

from config import configure_logging, DEFAULT_TURN_LIMIT_MINUTES, SYSTEM_PROMPT
from ollama_client import get_models, generate_response, OllamaClientError
from chat_manager import ConversationState


# Configure logging
configure_logging()


def initialize_session_state(models: list[str]) -> None:
    """Initialize Streamlit session state with default values."""
    if 'conversation' not in st.session_state:
        # Set default models
        agent1_default = models[0] if models else ""
        agent2_default = models[1] if len(models) > 1 else agent1_default

        st.session_state.conversation = None
        st.session_state.agent1_model = agent1_default
        st.session_state.agent2_model = agent2_default
        st.session_state.agent1_system_prompt = SYSTEM_PROMPT
        st.session_state.agent2_system_prompt = SYSTEM_PROMPT


def validate_inputs(agent1: str, agent2: str, topic: str) -> Optional[str]:
    """
    Validate user inputs.

    Returns:
        Error message if validation fails, None otherwise.
    """
    if not topic or not topic.strip():
        return "Please enter a topic for the agents to discuss."

    if agent1 == agent2:
        return "Please select different models for Agent 1 and Agent 2 to make the conversation more interesting."

    return None


def render_conversation_controls(
    models: list[str],
    is_running: bool,
    has_conversation: bool
) -> tuple[str, str, str, int, str, str]:
    """
    Render the conversation control UI elements.

    Returns:
        Tuple of (agent1_model, agent2_model, topic, turn_limit, agent1_system_prompt, agent2_system_prompt)
    """
    col1, col2 = st.columns(2)
    with col1:
        agent1_selection = st.selectbox(
            "Select Agent 1 Model",
            models,
            index=models.index(st.session_state.agent1_model) if st.session_state.agent1_model in models else 0,
            disabled=is_running,
            key="agent1_selectbox"
        )

    with col2:
        agent2_selection = st.selectbox(
            "Select Agent 2 Model",
            models,
            index=models.index(st.session_state.agent2_model) if st.session_state.agent2_model in models else 0,
            disabled=is_running,
            key="agent2_selectbox"
        )

    topic = st.text_area(
        "Enter a topic for the agents to discuss",
        disabled=is_running,
        placeholder="e.g., The benefits of artificial intelligence",
        key="topic_input",
        height=150
    )

    col1, col2 = st.columns(2)
    with col1:
        agent1_system_prompt = st.text_area(
            "Agent 1 System Prompt",
            value=st.session_state.agent1_system_prompt,
            disabled=is_running,
            height=150,
            help="Customize how Agent 1 should behave in the conversation.",
            key="agent1_system_prompt_input"
        )

    with col2:
        agent2_system_prompt = st.text_area(
            "Agent 2 System Prompt",
            value=st.session_state.agent2_system_prompt,
            disabled=is_running,
            height=150,
            help="Customize how Agent 2 should behave in the conversation.",
            key="agent2_system_prompt_input"
        )

    turn_limit = st.number_input(
        "Time limit in minutes (0 for unlimited)",
        min_value=0,
        value=DEFAULT_TURN_LIMIT_MINUTES,
        disabled=is_running,
        help="Set how long the conversation should run. Set to 0 for unlimited time.",
        key="turn_limit_input"
    )

    return agent1_selection, agent2_selection, topic, turn_limit, agent1_system_prompt, agent2_system_prompt


def render_action_buttons(
    conversation: Optional[ConversationState],
    topic: str,
    validation_error: Optional[str]
) -> tuple[bool, bool, bool]:
    """
    Render Start, Stop, and Continue buttons.

    Returns:
        Tuple of (start_clicked, stop_clicked, continue_clicked)
    """
    is_running = conversation is not None and conversation.is_running
    has_messages = conversation is not None and len(conversation.messages) > 0
    time_expired = conversation is not None and conversation.time_expired

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        start_disabled = (
            not topic or
            not topic.strip() or
            is_running or
            validation_error is not None
        )
        start_clicked = st.button(
            "Start",
            disabled=start_disabled,
            type="primary",
            use_container_width=True
        )

    with col2:
        stop_clicked = st.button(
            "Stop",
            disabled=not is_running,
            use_container_width=True
        )

    with col3:
        continue_clicked = st.button(
            "Continue",
            disabled=not time_expired,
            type="primary" if time_expired else "secondary",
            use_container_width=True
        )

    with col4:
        if conversation and conversation.start_time:
            elapsed_time = conversation.get_elapsed_time_str()
            limit_str = f"{conversation.turn_limit_minutes}m" if conversation.turn_limit_minutes > 0 else "∞"
            st.info(f"⏱️ Elapsed: {elapsed_time} / {limit_str}")

    return start_clicked, stop_clicked, continue_clicked


def render_messages(conversation: Optional[ConversationState]) -> None:
    """Render the conversation messages with auto-scroll."""
    if conversation is None or not conversation.messages:
        st.info("👋 Select models and enter a topic, then click 'Start' to begin the conversation.")
        return

    # Render all messages
    for message in conversation.messages:
        with st.chat_message(message.get_streamlit_role(), avatar=message.get_avatar()):
            timestamp = message.timestamp.strftime("%H:%M:%S")
            st.markdown(f"**{message.agent_name}** ({timestamp})")
            st.markdown(message.content)
    

def render_export_button(conversation: Optional[ConversationState]) -> None:
    """Render the chat export button."""
    if conversation is None or not conversation.messages:
        return

    chat_export = conversation.export_to_markdown()
    st.download_button(
        label="💾 Save Chat",
        data=chat_export,
        file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown",
        use_container_width=True
    )


def handle_conversation_loop(conversation: ConversationState) -> None:
    """Handle the main conversation loop."""
    # Check time limit
    if conversation.is_time_limit_reached():
        conversation.pause_for_time_limit()
        st.rerun()

    # Get the next agent to respond (we switch after getting the response)
    agent_name, agent_model = conversation.get_next_agent_info()
    #logging.info("Next agent to respond: %s, Model: %s", agent_name, agent_model)

    # Determine Streamlit role and avatar for the agent
    streamlit_role = "user" if agent_name == "Agent 1" else "assistant"
    avatar = "🤖" if agent_name == "Agent 1" else "🦾"

    # Display the agent's response in real-time
    with st.chat_message(streamlit_role, avatar=avatar):
        message_placeholder = st.empty()
        timestamp_placeholder = st.empty()

        full_response = ""

        try:
            # Get the system prompt for the current agent
            agent_number = 1 if agent_name == "Agent 1" else 2
            system_prompt = conversation.get_agent_system_prompt(agent_number)
            
            # Generate response
            for chunk in generate_response(
                agent_model, 
                conversation.get_messages_for_model(),
                system_prompt
            ):
            
                if not conversation.is_running:
                    #logging.info("Conversation stopped during generation")
                    break

                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            # Final display without cursor
            message_placeholder.markdown(full_response)

            # Validate response
            if not full_response or not full_response.strip():
                st.error(
                    f"❌ {agent_name} ({agent_model}) failed to generate a response. "
                    "The conversation has been stopped."
                )
                logging.warning("Model %s returned an empty response.", agent_model)
                conversation.stop_conversation()
                st.rerun()
                return

            # Only add message if still running
            if conversation.is_running:
                # Switch to the agent that just responded
                conversation.switch_agent()
                # Add the message
                conversation.add_message(full_response)

                # Display timestamp
                timestamp = conversation.messages[-1].timestamp.strftime("%H:%M:%S")
                timestamp_placeholder.markdown(f"**{agent_name}** ({timestamp})")

                st.rerun()

        except OllamaClientError as e:
            st.error(f"❌ Error: {e}")
            conversation.stop_conversation()
            st.rerun()


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="Chatting Agents",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.title("🤖 Chatting Agents")
    
    # Fetch available models
    try:
        models = get_models()
    except OllamaClientError as e:
        st.error(f"❌ {e}")
        st.info("Make sure Ollama is running: `ollama serve`")
        st.stop()

    # Check if any models are available
    if not models or len(models) == 0:
        st.error("❌ No Ollama models found!")
        st.info(
            "You need to pull at least one model to use this application.\n\n"
            "To pull models, run:\n"
            "```bash\n"
            "ollama pull llama2\n"
            "ollama pull mistral\n"
            "```\n\n"
            "Then refresh this page."
        )
        st.stop()

    # Initialize session state
    initialize_session_state(models)

    # Get current conversation
    conversation = st.session_state.conversation

    # Render controls
    agent1_model, agent2_model, topic, turn_limit, agent1_system_prompt, agent2_system_prompt = render_conversation_controls(
        models,
        is_running=conversation is not None and conversation.is_running,
        has_conversation=conversation is not None
    )

    # Update session state
    st.session_state.agent1_model = agent1_model
    st.session_state.agent2_model = agent2_model
    st.session_state.agent1_system_prompt = agent1_system_prompt
    st.session_state.agent2_system_prompt = agent2_system_prompt

    # Validate inputs
    validation_error = validate_inputs(agent1_model, agent2_model, topic)
    if validation_error:
        st.warning(f"⚠️ {validation_error}")

    # Render action buttons
    start_clicked, stop_clicked, continue_clicked = render_action_buttons(conversation, topic, validation_error)

    # Show time expired warning
    if conversation and conversation.time_expired:
        st.warning("⏰ Time limit reached. Click 'Continue' to keep the conversation going.")

    # Handle button clicks
    if start_clicked and not validation_error:
        #logging.info("Starting new conversation on topic: %s", topic)
        st.session_state.conversation = ConversationState(
            agent1_model=agent1_model,
            agent2_model=agent2_model,
            topic=topic,
            turn_limit_minutes=turn_limit,
            agent1_system_prompt=agent1_system_prompt,
            agent2_system_prompt=agent2_system_prompt
        )
        st.session_state.conversation.start_conversation()
        st.rerun()

    if stop_clicked and conversation:
        #logging.info("Stopping conversation")
        conversation.stop_conversation()
        st.rerun()

    if continue_clicked and conversation:
        #logging.info("Continuing conversation after time limit")
        conversation.continue_conversation()
        st.rerun()

    st.divider()

    # Render messages
    render_messages(conversation)

    # Render export button in sidebar
    with st.sidebar:
        st.header("💾 Export")
        render_export_button(conversation)

        if conversation and conversation.messages:
            st.divider()
            st.subheader("📊 Conversation Stats")
            st.metric("Total Messages", len(conversation.messages))
            st.metric("Duration", conversation.get_elapsed_time_str())

    # Main conversation loop
    if conversation and conversation.is_running:
        handle_conversation_loop(conversation)


if __name__ == "__main__":
    main()
