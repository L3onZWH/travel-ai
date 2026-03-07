from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    data: str  # human-readable result / error message
    raw: dict | None = None  # structured payload for further processing


class BaseTool(ABC):
    """All tools must inherit from this class."""

    #: Unique name used by Claude tool_use
    name: str
    #: One-line description shown to the LLM
    description: str
    #: JSON Schema of the tool's parameters
    parameters: dict

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        ...

    def to_claude_schema(self) -> dict:
        """Return the dict expected by Anthropic's tools array."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }
