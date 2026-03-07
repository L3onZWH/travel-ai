from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from agent.prompts import SYSTEM_PROMPT
from agent.rules import RulesEngine
from agent.workspace import WorkspaceManager
from llm.anthropic_llm import AnthropicLLM
from memory.manager import MemoryManager
from tools.knowledge_base import KnowledgeBaseTool
from tools.registry import ToolRegistry
from tools.web_search import WebSearchTool

if TYPE_CHECKING:
    pass


class TravelAgent:
    """
    主 Agent：联结 LLM、Memory、Rules 和 Tools。
    每个实例与一个 Workspace + Session 绑定。
    """

    def __init__(
        self,
        session_id: str = "",
        workspace: WorkspaceManager | None = None,
        title: str = "",
    ) -> None:
        self._workspace = workspace or WorkspaceManager.create(WorkspaceManager.DEFAULT)
        self._memory = MemoryManager(
            session_id=session_id,
            workspace=self._workspace,
            title=title,
        )
        self._rules = RulesEngine()
        self._registry = ToolRegistry()
        self._llm = AnthropicLLM(tool_registry=self._registry)

        # 注册内置工具
        self._registry.register(WebSearchTool())
        self._registry.register(KnowledgeBaseTool())

    # ------------------------------------------------------------------ #
    @property
    def session_id(self) -> str:
        return self._memory.session_id

    @property
    def workspace(self) -> WorkspaceManager:
        return self._workspace

    @property
    def title(self) -> str:
        return self._memory.title

    # ------------------------------------------------------------------ #
    def _build_system_prompt(self) -> str:
        parts = [SYSTEM_PROMPT]
        rules_block = self._rules.as_system_block()
        if rules_block:
            parts.append(rules_block)
        profile = self._memory.load_profile()
        if profile:
            import json
            parts.append(
                "## 用户画像\n"
                + json.dumps(profile, ensure_ascii=False, indent=2)
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------ #
    def chat(self, user_input: str) -> str:
        """Single-turn: add user message, call LLM, return assistant text."""
        self._memory.add_message("user", user_input)
        system = self._build_system_prompt()
        messages = self._memory.get_messages()
        response_text = self._llm.chat(system=system, messages=messages)
        self._memory.add_message("assistant", response_text)
        return response_text

    def stream(self, user_input: str) -> Iterator[str]:
        """Streaming variant — yields text chunks as they arrive."""
        self._memory.add_message("user", user_input)
        system = self._build_system_prompt()
        messages = self._memory.get_messages()
        collected: list[str] = []
        for chunk in self._llm.stream(system=system, messages=messages):
            collected.append(chunk)
            yield chunk
        self._memory.add_message("assistant", "".join(collected))

    # ------------------------------------------------------------------ #
    def set_title(self, title: str) -> None:
        self._memory.set_title(title)

    def update_profile(self, updates: dict) -> dict:
        return self._memory.update_profile(updates)

    def clear_history(self) -> None:
        self._memory.clear_history()

    def get_save_path(self) -> str:
        """Return human-friendly path to the session directory."""
        return str(self._memory.session_dir)

