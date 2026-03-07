from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent.workspace import WorkspaceManager


@dataclass
class SessionInfo:
    session_id: str
    workspace: str
    title: str
    created_at: str
    message_count: int
    session_dir: Path

    @property
    def display_name(self) -> str:
        """Human-friendly label: title if set, else session_id."""
        return self.title if self.title else self.session_id

    @property
    def short_id(self) -> str:
        """First 12 chars of session_id for compact display."""
        return self.session_id[:12]


class SessionManager:
    """列出、检索和加载指定 Workspace 下的 Session。"""

    def __init__(self, workspace: WorkspaceManager) -> None:
        self._workspace = workspace

    # ------------------------------------------------------------------ #
    def list_sessions(self, limit: int = 20) -> list[SessionInfo]:
        """Return recent sessions, newest first."""
        sessions_dir = self._workspace.sessions_dir
        if not sessions_dir.exists():
            return []

        dirs = sorted(
            (d for d in sessions_dir.iterdir() if d.is_dir()),
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )[:limit]

        result: list[SessionInfo] = []
        for d in dirs:
            meta = self._load_meta(d)
            history = self._load_history(d)
            result.append(
                SessionInfo(
                    session_id=d.name,
                    workspace=self._workspace.name,
                    title=meta.get("title", ""),
                    created_at=meta.get("created_at", ""),
                    message_count=len(history),
                    session_dir=d,
                )
            )
        return result

    # ------------------------------------------------------------------ #
    def load_history(self, session_id: str) -> list[dict]:
        """Return raw LLM message list for the given session_id."""
        d = self._workspace.sessions_dir / session_id
        if not d.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        return self._load_history(d)

    def session_exists(self, session_id: str) -> bool:
        return (self._workspace.sessions_dir / session_id).is_dir()

    def session_dir(self, session_id: str) -> Path:
        return self._workspace.sessions_dir / session_id

    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_meta(session_dir: Path) -> dict:
        meta_file = session_dir / "meta.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
        return {}

    @staticmethod
    def _load_history(session_dir: Path) -> list[dict]:
        history_file = session_dir / "history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
            except Exception:  # noqa: BLE001
                pass
        return []
