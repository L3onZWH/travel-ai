from __future__ import annotations

from pathlib import Path

from config.settings import settings


class WorkspaceManager:
    """
    代表一个隔离的工作区，每个 Workspace 有独立的 sessions/ 和 memory/ 目录。

    目录结构:
        workspace/<name>/
            sessions/<session_id>/
                history.json       # LLM 消息列表（结构化）
                conversation.md    # 对话历史（可读）
                meta.json          # Session 元数据
            memory/
                user_profile.json  # 用户画像（跨 Session）
    """

    DEFAULT = "default"

    def __init__(self, name: str = DEFAULT) -> None:
        # 清洁 workspace 名：小写、空格转下划线
        self.name = (name or self.DEFAULT).strip().lower().replace(" ", "_")
        self._root: Path = settings.workspace_dir / self.name

    # ------------------------------------------------------------------ #
    @property
    def root(self) -> Path:
        return self._root

    @property
    def sessions_dir(self) -> Path:
        return self._root / "sessions"

    @property
    def memory_dir(self) -> Path:
        return self._root / "memory"

    # ------------------------------------------------------------------ #
    def ensure_dirs(self) -> None:
        """Create workspace directories if missing."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    @staticmethod
    def list_all() -> list[str]:
        """Return names of all existing workspaces (sorted)."""
        base = settings.workspace_dir
        if not base.exists():
            return []
        return sorted(
            d.name
            for d in base.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    @classmethod
    def create(cls, name: str = DEFAULT) -> WorkspaceManager:
        """Create workspace directories and return manager."""
        ws = cls(name)
        ws.ensure_dirs()
        return ws

    # ------------------------------------------------------------------ #
    def __repr__(self) -> str:
        return f"WorkspaceManager(name={self.name!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, WorkspaceManager):
            return self.name == other.name
        return NotImplemented
