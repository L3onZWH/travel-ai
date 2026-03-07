"""Unit tests for agent/session.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.session import SessionInfo, SessionManager
from agent.workspace import WorkspaceManager


def _make_session(ws: WorkspaceManager, session_id: str, title: str = "", msgs: int = 2) -> Path:
    """Helper: create a minimal session directory with meta + history."""
    d = ws.sessions_dir / session_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(
        json.dumps({"session_id": session_id, "workspace": ws.name,
                    "title": title, "created_at": "2025-01-01T10:00:00"}),
        encoding="utf-8",
    )
    history = [{"role": "user", "content": f"msg {i}"} for i in range(msgs)]
    (d / "history.json").write_text(json.dumps(history), encoding="utf-8")
    return d


class TestSessionManagerList:
    def test_empty_workspace_returns_empty_list(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        assert sm.list_sessions() == []

    def test_lists_created_sessions(self, tmp_workspace):
        _make_session(tmp_workspace, "ses_001", title="Tokyo Trip")
        sm = SessionManager(tmp_workspace)
        sessions = sm.list_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == "ses_001"
        assert sessions[0].title == "Tokyo Trip"

    def test_message_count_correct(self, tmp_workspace):
        _make_session(tmp_workspace, "ses_002", msgs=5)
        sm = SessionManager(tmp_workspace)
        assert sm.list_sessions()[0].message_count == 5

    def test_multiple_sessions(self, tmp_workspace):
        for i in range(3):
            _make_session(tmp_workspace, f"ses_{i:03d}")
        sm = SessionManager(tmp_workspace)
        assert len(sm.list_sessions()) == 3


class TestSessionManagerLoad:
    def test_load_history_returns_messages(self, tmp_workspace):
        _make_session(tmp_workspace, "ses_load", msgs=3)
        sm = SessionManager(tmp_workspace)
        history = sm.load_history("ses_load")
        assert len(history) == 3
        assert history[0]["role"] == "user"

    def test_load_history_raises_for_missing_session(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        with pytest.raises(FileNotFoundError):
            sm.load_history("nonexistent_session")

    def test_session_exists_true(self, tmp_workspace):
        _make_session(tmp_workspace, "ses_ex")
        sm = SessionManager(tmp_workspace)
        assert sm.session_exists("ses_ex") is True

    def test_session_exists_false(self, tmp_workspace):
        sm = SessionManager(tmp_workspace)
        assert sm.session_exists("nope") is False


class TestSessionInfo:
    def _make_info(self, session_id="20250101_120000", title="") -> SessionInfo:
        return SessionInfo(
            session_id=session_id,
            workspace="test",
            title=title,
            created_at="2025-01-01T12:00:00",
            message_count=4,
            session_dir=Path("/tmp/fake"),
        )

    def test_short_id_is_12_chars(self):
        info = self._make_info("abcdef123456789")
        assert info.short_id == "abcdef123456"

    def test_display_name_uses_title_when_set(self):
        info = self._make_info(title="My Trip")
        assert info.display_name == "My Trip"

    def test_display_name_falls_back_to_session_id(self):
        info = self._make_info(session_id="ses_fallback", title="")
        assert info.display_name == "ses_fallback"
