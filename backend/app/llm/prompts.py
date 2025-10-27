"""Prompt template loading and rendering"""
import os
import yaml
from typing import Dict, Any, Optional
from string import Template


class PromptTemplate:
    """Represents a prompt template with metadata"""

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.description = data.get("description", "")
        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt", "")
        self.structured_output = data.get("structured_output")
        self.temperature = data.get("temperature", 1.0)
        self.model = data.get("model", "planning")  # Default to planning model

    def render_user_prompt(self, **kwargs) -> str:
        """Render user prompt with provided parameters"""
        template = Template(self.user_prompt_template)
        return template.safe_substitute(**kwargs)


class PromptLoader:
    """Loads and manages prompt templates"""

    def __init__(self, prompts_dir: str):
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}

    def load(self, prompt_name: str) -> PromptTemplate:
        """Load a prompt template by name"""
        if prompt_name in self._cache:
            return self._cache[prompt_name]

        file_path = os.path.join(self.prompts_dir, f"{prompt_name}.yaml")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Prompt template not found: {file_path}")

        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        template = PromptTemplate(data)
        self._cache[prompt_name] = template
        return template


# Global loader instance
_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get or create the global prompt loader"""
    global _loader
    if _loader is None:
        # Get the base directory (backend/)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompts_dir = os.path.join(base_dir, "knowledge", "prompts")
        _loader = PromptLoader(prompts_dir)
    return _loader
