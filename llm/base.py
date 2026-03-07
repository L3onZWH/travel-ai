from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # "end_turn" | "tool_use"


class BaseLLM(ABC):
    """Abstract interface for LLM backends."""

    def chat(
        self,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> str:
        """Send messages, handle tool loops, return final text (blocking)."""
        raise NotImplementedError

    def stream(
        self,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> Iterator[str]:
        """Yield text tokens as they arrive."""
        raise NotImplementedError

    def raw_chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        """Low-level call returning structured LLMResponse."""
        raise NotImplementedError

