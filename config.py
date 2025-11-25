"""Configuration module for the chatting agent application."""
import os
import logging
from typing import Optional

# Ollama configuration
OLLAMA_HOST: str = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# System prompt for the agents
SYSTEM_PROMPT: str = os.getenv(
    'SYSTEM_PROMPT',
    "Engage in thoughtful, productive discussions. Share insights, consider different perspectives, "
    "and build upon each other's ideas. Keep responses concise and focused on the topic."
)

# Logging configuration
LOG_FILE: str = os.getenv('LOG_FILE', 'app.log')
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT: str = '%(asctime)s - %(levelname)s - %(message)s'

# Default values
DEFAULT_TURN_LIMIT_MINUTES: int = 5
DEFAULT_TOPIC: str = ""


def configure_logging() -> None:
    """Configure the logging system with settings from environment variables."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        filename=LOG_FILE,
        level=level,
        format=LOG_FORMAT
    )
