"""Configuration module for the chatting agent application."""
import os
import logging
from typing import Optional

# Ollama configuration
OLLAMA_HOST: str = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# System prompt for the agents
SYSTEM_PROMPT: str = os.getenv(
    'SYSTEM_PROMPT',
    "Chat like friends about any topic. Keep it casual, light, sometimes funny. "
    "Stay safe and respectful."
)

# Logging configuration
LOG_FILE: str = os.getenv('LOG_FILE', 'app.log')
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT: str = '%(asctime)s - %(levelname)s - %(message)s'

# Default values
DEFAULT_TURN_LIMIT_MINUTES: int = 10
DEFAULT_TOPIC: str = ""


def configure_logging() -> None:
    """Configure the logging system with settings from environment variables."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        filename=LOG_FILE,
        level=level,
        format=LOG_FORMAT
    )
