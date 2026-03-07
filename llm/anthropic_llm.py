from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, TypedDict

import anthropic

from config.settings import settings
from llm.base import BaseLLM, LLMResponse, ToolCall

if TYPE_CHECKING:
    from tools.registry import ToolRegistry


class _ToolCallEntry(TypedDict):
    id: str
    name: str
    input: dict[str, object]


class AnthropicLLM(BaseLLM):
    """Claude backend with agentic tool-calling loop."""

    MAX_TOOL_ROUNDS = 8  # safety cap against infinite loops

    def __init__(
        self,
        model: str | None = None,
        tool_registry: ToolRegistry | None = None,
    ):
        self._model = model or settings.anthropic_model
        client_kwargs: dict = {"api_key": settings.anthropic_api_key}
        if settings.anthropic_base_url:
            client_kwargs["base_url"] = settings.anthropic_base_url
        self._client = anthropic.Anthropic(**client_kwargs)
        self._registry = tool_registry

    # ------------------------------------------------------------------ #
    def _raw_call(
        self, messages: list[dict], system: str, tools: list[dict]
    ) -> anthropic.types.Message:
        kwargs: dict = dict(
            model=self._model,
            max_tokens=settings.max_tokens,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        return self._client.messages.create(**kwargs)

    def _tools_schema(self) -> list[dict]:
        if self._registry is None:
            return []
        return self._registry.to_claude_schema()

    def _run_tool(self, name: str, inputs: dict) -> str:
        if self._registry is None:
            return "[Tool registry not available]"
        tool = self._registry.get(name)
        if tool is None:
            return f"[Unknown tool: {name}]"
        result = tool.execute(**inputs)
        if result.success:
            return result.data
        return f"[Tool error] {result.data}"

    # ------------------------------------------------------------------ #
    def chat(
        self,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> str:
        """Run agentic loop until end_turn or tool rounds exhausted."""
        msgs = list(messages or [])
        tools = self._tools_schema()

        for _ in range(self.MAX_TOOL_ROUNDS):
            response = self._raw_call(msgs, system, tools)

            if response.stop_reason == "end_turn" or response.stop_reason is None:
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Build assistant turn with full content blocks (required by Anthropic)
                assistant_content: list[dict[str, object]] = []
                tool_calls_in_turn: list[_ToolCallEntry] = []

                for block in response.content:
                    if block.type == "text":
                        assistant_content.append({"type": "text", "text": block.text})
                    elif block.type == "tool_use":
                        assistant_content.append(
                            {
                                "type": "tool_use",
                                "id": block.id,
                                "name": block.name,
                                "input": block.input,
                            }
                        )
                        tool_calls_in_turn.append(
                            _ToolCallEntry(id=block.id, name=block.name, input=block.input)
                        )

                msgs.append({"role": "assistant", "content": assistant_content})

                # Execute each tool and collect results
                tool_results = []
                for tc in tool_calls_in_turn:
                    output = self._run_tool(tc["name"], tc["input"])
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tc["id"],
                            "content": output,
                        }
                    )

                msgs.append({"role": "user", "content": tool_results})
                continue

            # Unknown stop reason — just return whatever text we have
            return self._extract_text(response)

        # Ran out of rounds
        return "[Max tool rounds reached — partial response above]"

    # ------------------------------------------------------------------ #
    def stream(
        self,
        system: str = "",
        messages: list[dict] | None = None,
    ) -> Iterator[str]:
        """Stream the final LLM reply (tool calls are resolved silently first)."""
        msgs = list(messages or [])
        tools = self._tools_schema()

        # Resolve tool calls silently first if we have tools
        if tools:
            # Run the non-streaming loop up to the last assistant turn
            pre_text = self.chat(system=system, messages=msgs)
            yield pre_text
            return

        # No tools — pure streaming
        kwargs: dict = dict(
            model=self._model,
            max_tokens=settings.max_tokens,
            messages=msgs,
        )
        if system:
            kwargs["system"] = system

        with self._client.messages.stream(**kwargs) as stream_obj:
            yield from stream_obj.text_stream

    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        parts = [b.text for b in response.content if b.type == "text"]
        return "\n".join(parts).strip()

    # ------------------------------------------------------------------ #
    # Legacy raw interface (used by tests or direct callers)
    def raw_chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        response = self._raw_call(messages, system, tools or [])
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input))
        return LLMResponse(
            content="\n".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason or "end_turn",
        )
