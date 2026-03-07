"""Integration tests: Workspace isolation."""
from __future__ import annotations

from unittest.mock import patch

from agent.core import TravelAgent
from agent.session import SessionManager
from agent.workspace import WorkspaceManager


class TestWorkspaceIsolation:
    def test_different_workspaces_have_different_roots(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws1 = WorkspaceManager.create("ws1")
        ws2 = WorkspaceManager.create("ws2")
        assert ws1.root != ws2.root
        assert ws1.sessions_dir != ws2.sessions_dir

    def test_sessions_in_workspace_a_not_visible_in_b(self, tmp_path, monkeypatch, mock_llm):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws_a = WorkspaceManager.create("ws_a")
        ws_b = WorkspaceManager.create("ws_b")

        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            agent_a = TravelAgent(session_id="shared_id", workspace=ws_a)
        agent_a.chat("ws_a message")

        sm_b = SessionManager(ws_b)
        sessions_in_b = sm_b.list_sessions()
        assert all(s.session_id != "shared_id" for s in sessions_in_b)

    def test_profiles_are_isolated_per_workspace(self, tmp_path, monkeypatch, mock_llm):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws_a = WorkspaceManager.create("ws_a2")
        ws_b = WorkspaceManager.create("ws_b2")

        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            agent_a = TravelAgent(workspace=ws_a)
            agent_b = TravelAgent(workspace=ws_b)

        agent_a.update_profile({"name": "Alice"})
        profile_b = agent_b._memory.load_profile()
        assert profile_b.get("name") != "Alice"
