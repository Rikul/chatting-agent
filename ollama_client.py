"""Ollama API client for interacting with language models."""
import json
import logging
from typing import List, Dict, Iterator, Optional

import requests

from config import OLLAMA_HOST, SYSTEM_PROMPT


class OllamaClientError(Exception):
    """Custom exception for Ollama client errors."""
    pass


def get_models() -> List[str]:
    """
    Fetch available models from the Ollama instance.

    Returns:
        List of model names available from Ollama.

    Raises:
        OllamaClientError: If unable to connect to Ollama or fetch models.
    """
    try:
        #logging.info("Attempting to connect to Ollama at %s", OLLAMA_HOST)
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        response.raise_for_status()

        models_data = response.json()

        # Return empty list if no models are installed (let the UI handle this gracefully)
        if "models" not in models_data or not models_data["models"]:
            #logging.warning("Connected to Ollama but no models found")
            return []

        models = [m['name'] for m in models_data["models"]]
        #logging.info("Successfully connected to Ollama. Found %d models.", len(models))
        return models

    except requests.exceptions.RequestException as e:
        logging.error("Failed to connect to Ollama: %s", e, exc_info=True)
        raise OllamaClientError(
            f"Ollama is not running or not reachable at {OLLAMA_HOST}. "
            f"Please check the logs for more details. Error: {e}"
        ) from e


def generate_response(
    model: str,
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None
) -> Iterator[str]:
    """
    Generate a streaming response from an Ollama model.

    Args:
        model: The name of the model to use for generation.
        messages: List of message dictionaries with 'role' and 'content' keys.
        system_prompt: Optional system prompt to override the default.

    Yields:
        String chunks of the model's response.

    Raises:
        OllamaClientError: If there's an error communicating with the model.
    """
    # Create a clean version of the messages for the model
    # Convert to user/assistant roles (last message is user, others are assistant)
    model_messages = []
    for i, msg in enumerate(messages):
        role = "user" if i == len(messages) - 1 else "assistant"
        model_messages.append({"role": role, "content": msg["content"]})

    #logging.info("Sending prompt to %s with %d messages", model, len(model_messages))

    payload = {
        "model": model,
        "messages": model_messages,
        "stream": True,
        "system": system_prompt or SYSTEM_PROMPT,
    }

    try:
        with requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    try:
                        json_line = json.loads(line)
                        if "message" in json_line and "content" in json_line["message"]:
                            yield json_line["message"]["content"]
                    except json.JSONDecodeError:
                        logging.warning("Received non-JSON line from stream: %s", line)

    except requests.exceptions.RequestException as e:
        logging.error("Error during API call to %s: %s", model, e, exc_info=True)
        raise OllamaClientError(
            f"An error occurred while communicating with the model {model}: {e}"
        ) from e
