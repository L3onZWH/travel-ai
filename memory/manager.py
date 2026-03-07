from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.workspace import WorkspaceManager


class MemoryManager:
    """
    持久化对话历史和用户画像到磁盘。

    目录结构（在 workspace 隔离下）:
        sessions/<session_id>/
            history.json       – LLM 消息列表（结构化，API 直接使用）
            conversation.md    – 对话历史可读版
            meta.json          – Session 元数据
        memory/
            user_profile.json  – 用户画像（跨 Session）
    """

    _PROFILE_FILE = "user_profile.json"

    def __init__(
        self,
        session_id: str = "",
        workspace: WorkspaceManager | None = None,
        title: str = "",
    ) -> None:
        from agent.workspace import WorkspaceManager

        self._workspace = workspace or WorkspaceManager.create(WorkspaceManager.DEFAULT)
        self._session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self._title = title
        self._created_at = datetime.now().isoformat(timespec="seconds")

        self._session_dir: Path = self._workspace.sessions_dir / self._session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)

        self._history_path = self._session_dir / "history.json"
        self._conv_path = self._session_dir / "conversation.md"
        self._meta_path = self._session_dir / "meta.json"
        self._profile_path = self._workspace.memory_dir / self._PROFILE_FILE

        self._messages: list[dict] = self._load_history()
        self._init_meta()

    # ------------------------------------------------------------------ #
    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def title(self) -> str:
        return self._title

    # ------------------------------------------------------------------ #
    # Meta
    # ------------------------------------------------------------------ #
    def _init_meta(self) -> None:
        """Write meta.json on first creation; skip if already exists."""
        if self._meta_path.exists():
            existing = json.loads(self._meta_path.read_text(encoding="utf-8"))
            self._title = self._title or existing.get("title", "")
            self._created_at = existing.get("created_at", self._created_at)
            return
        self._save_meta()

    def _save_meta(self) -> None:
        meta = {
            "session_id": self._session_id,
            "workspace": self._workspace.name,
            "title": self._title,
            "created_at": self._created_at,
        }
        self._meta_path.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def set_title(self, title: str) -> None:
        self._title = title
        self._save_meta()

    # ------------------------------------------------------------------ #
    # History (JSON — LLM 直接读写)
    # ------------------------------------------------------------------ #
    def _load_history(self) -> list[dict]:
        if self._history_path.exists():
            try:
                data = json.loads(self._history_path.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
            except Exception:  # noqa: BLE001
                return []
        return []

    def _save_history(self) -> None:
        self._history_path.write_text(
            json.dumps(self._messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------ #
    # conversation.md — 人类可读版
    # ------------------------------------------------------------------ #
    def _append_conv_md(self, role: str, content: str) -> None:
        """Append one message block to conversation.md."""
        if not self._conv_path.exists():
            header = (
                f"# Session: {self._title or self._session_id}\n"
                f"- Workspace: {self._workspace.name}\n"
                f"- 创建时间: {self._created_at}\n\n"
                f"## 对话记录\n"
            )
            self._conv_path.write_text(header, encoding="utf-8")

        label = "User" if role == "user" else "Assistant"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = f"\n### [{label}] {ts}\n{content}\n"
        with self._conv_path.open("a", encoding="utf-8") as f:
            f.write(block)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def add_message(self, role: str, content: str | list) -> None:
        self._messages.append({"role": role, "content": content})
        self._save_history()
        # 对话 MD 仅记录文字内容
        if isinstance(content, str):
            self._append_conv_md(role, content)

    def get_messages(self, window: int | None = None) -> list[dict]:
        """Return last *window* messages (or all if window is None)."""
        if window:
            return self._messages[-window:]
        return list(self._messages)

    def clear_history(self) -> None:
        self._messages = []
        self._save_history()
        # 重置 conversation.md
        if self._conv_path.exists():
            self._conv_path.unlink()

    # ------------------------------------------------------------------ #
    # User profile
    # ------------------------------------------------------------------ #
    def load_profile(self) -> dict:
        if self._profile_path.exists():
            try:
                return json.loads(self._profile_path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                return {}
        return {}

    def save_profile(self, profile: dict) -> None:
        self._workspace.memory_dir.mkdir(parents=True, exist_ok=True)
        self._profile_path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update_profile(self, updates: dict) -> dict:
        profile = self.load_profile()
        profile.update(updates)
        self.save_profile(profile)
        return profile

    # ------------------------------------------------------------------ #
    # Convenience
    # ------------------------------------------------------------------ #
    @property
    def session_dir(self) -> Path:
        return self._session_dir

    @property
    def conv_md_path(self) -> Path:
        return self._conv_path

