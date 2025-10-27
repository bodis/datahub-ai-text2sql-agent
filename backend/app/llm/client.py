"""Anthropic Claude client with structured output support"""
import os
import json
import logging
import time
import sys
from typing import Type, TypeVar, Optional, List, Dict, Any, Tuple
from anthropic import Anthropic
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - force to stdout with formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar('T', bound=BaseModel)


class ConversationMessage:
    """Represents a message in the conversation history"""
    def __init__(self, role: str, content: str):
        self.role = role  # 'user' or 'assistant'
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class ClaudeClient:
    """Client for interacting with Anthropic Claude API"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # Load model configurations
        self.weak_model = os.getenv("ANTHROPIC_WEAK_MODEL", "claude-haiku-4-5")
        self.planning_model = os.getenv("ANTHROPIC_PLANNING_MODEL", "claude-sonnet-4-5-20250929")
        self.developer_model = os.getenv("ANTHROPIC_DEVELOPER_MODEL", "claude-sonnet-4-5-20250929")

        self.max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
        self.debug_enabled = os.getenv("LLM_DEBUG", "false").lower() == "true"

        self.client = Anthropic(api_key=self.api_key)

    def get_model_by_name(self, model_name: str) -> str:
        """Get model ID by name (weak, planning, developer)"""
        model_map = {
            "weak": self.weak_model,
            "planning": self.planning_model,
            "developer": self.developer_model
        }
        return model_map.get(model_name, self.planning_model)

    def complete(
        self,
        messages: List[ConversationMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        model: Optional[str] = None
    ) -> Tuple[str, Dict[str, int]]:
        """
        Send a completion request without structured output

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            model: Model to use (or model name: weak/planning/developer)

        Returns:
            Tuple of (response text, token usage dict)
        """
        # Resolve model
        model_id = self.get_model_by_name(model) if model else self.planning_model

        formatted_messages = [msg.to_dict() for msg in messages]

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": self.max_tokens,
            "messages": formatted_messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Debug logging
        if self.debug_enabled:
            logger.info("=" * 80)
            logger.info(f"LLM REQUEST - Model: {model_id}")
            logger.info(f"Temperature: {temperature}")
            if system_prompt:
                logger.info(f"SYSTEM PROMPT (FULL):\n{system_prompt}")
            logger.info(f"USER MESSAGES (FULL):")
            for i, msg in enumerate(formatted_messages):
                logger.info(f"  Message {i+1} [{msg['role']}]:\n{msg['content']}")
            logger.info("=" * 80)

        start_time = time.time()
        response = self.client.messages.create(**kwargs)
        elapsed_time = time.time() - start_time

        # Extract usage
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            "elapsed_time_ms": int(elapsed_time * 1000)
        }

        # Extract text content
        response_text = ""
        if response.content and len(response.content) > 0:
            response_text = response.content[0].text

        # Debug logging
        if self.debug_enabled:
            logger.info("=" * 80)
            logger.info(f"LLM RESPONSE - Model: {model_id}")
            logger.info(f"Elapsed Time: {elapsed_time:.2f}s ({usage['elapsed_time_ms']}ms)")
            logger.info(f"Token Usage: Input={usage['input_tokens']}, Output={usage['output_tokens']}, Total={usage['total_tokens']}")
            logger.info(f"RESPONSE TEXT (FULL):\n{response_text}")
            logger.info("=" * 80)

        return response_text, usage

    def complete_structured(
        self,
        messages: List[ConversationMessage],
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        model: Optional[str] = None
    ) -> Tuple[T, Dict[str, Any]]:
        """
        Send a completion request with structured output using tool use

        Args:
            messages: List of conversation messages
            response_model: Pydantic model for structured output
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            model: Model to use (or model name: weak/planning/developer)

        Returns:
            Tuple of (structured response, token usage dict)
        """
        # Resolve model
        model_id = self.get_model_by_name(model) if model else self.planning_model

        # Convert Pydantic model to tool schema
        tool_schema = self._pydantic_to_tool_schema(response_model)

        formatted_messages = [msg.to_dict() for msg in messages]

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "max_tokens": self.max_tokens,
            "messages": formatted_messages,
            "temperature": temperature,
            "tools": [tool_schema],
            "tool_choice": {"type": "tool", "name": tool_schema["name"]}
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Debug logging
        if self.debug_enabled:
            logger.info("=" * 80)
            logger.info(f"LLM STRUCTURED REQUEST - Model: {model_id}")
            logger.info(f"Response Model: {response_model.__name__}")
            logger.info(f"Temperature: {temperature}")
            if system_prompt:
                logger.info(f"SYSTEM PROMPT (FULL):\n{system_prompt}")
            logger.info(f"USER MESSAGES (FULL):")
            for i, msg in enumerate(formatted_messages):
                logger.info(f"  Message {i+1} [{msg['role']}]:\n{msg['content']}")
            logger.info("=" * 80)

        start_time = time.time()
        response = self.client.messages.create(**kwargs)
        elapsed_time = time.time() - start_time

        # Extract tool use from response
        structured_response = None
        tool_input = None
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_input = content_block.input
                break

        if tool_input is None:
            logger.error("No tool use found in response!")
            logger.error(f"Response content blocks: {[block.type for block in response.content]}")
            raise ValueError("No tool use found in response")

        # Log raw tool input before validation
        logger.info("=" * 80)
        logger.info(f"RAW TOOL INPUT (before validation):")
        logger.info(json.dumps(tool_input, indent=2))
        logger.info("=" * 80)

        # Parse the tool input as the structured response
        try:
            structured_response = response_model.model_validate(tool_input)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"VALIDATION ERROR for {response_model.__name__}:")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Tool input that failed validation:")
            logger.error(json.dumps(tool_input, indent=2))
            logger.error("=" * 80)
            raise

        # Build usage dict with full communication details
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            "elapsed_time_ms": int(elapsed_time * 1000),
            "communication": {
                "model": model_id,
                "system_prompt": system_prompt,
                "messages": formatted_messages,
                "response": tool_input,
                "temperature": temperature
            }
        }

        # Debug logging
        if self.debug_enabled:
            logger.info("=" * 80)
            logger.info(f"LLM STRUCTURED RESPONSE - Model: {model_id}")
            logger.info(f"Elapsed Time: {elapsed_time:.2f}s ({usage['elapsed_time_ms']}ms)")
            logger.info(f"Token Usage: Input={usage['input_tokens']}, Output={usage['output_tokens']}, Total={usage['total_tokens']}")
            logger.info(f"STRUCTURED RESPONSE (FULL):\n{json.dumps(structured_response.model_dump(), indent=2)}")
            logger.info("=" * 80)

        return structured_response, usage

    def _pydantic_to_tool_schema(self, model: Type[BaseModel]) -> Dict[str, Any]:
        """Convert Pydantic model to Anthropic tool schema"""
        schema = model.model_json_schema()

        # Remove schema-specific fields that Anthropic doesn't need
        schema.pop("title", None)
        schema.pop("$defs", None)

        return {
            "name": f"provide_{model.__name__.lower()}",
            "description": f"Provide structured {model.__name__}",
            "input_schema": schema
        }


# Global client instance
_client: Optional[ClaudeClient] = None


def get_client() -> ClaudeClient:
    """Get or create the global Claude client instance"""
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
