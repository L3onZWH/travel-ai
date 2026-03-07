"""Unit tests for agent/workspace.py."""
from __future__ import annotations

from agent.workspace import WorkspaceManager


class TestWorkspaceCreation:
    def test_create_returns_instance(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager.create("myws")
        assert isinstance(ws, WorkspaceManager)
        assert ws.name == "myws"

    def test_create_makes_sessions_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager.create("myws")
        assert ws.sessions_dir.is_dir()

    def test_create_makes_memory_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager.create("myws")
        assert ws.memory_dir.is_dir()


class TestWorkspaceNameSanitization:
    def test_lowercase(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager("MyWorkspace")
        assert ws.name == "myworkspace"

    def test_spaces_to_underscores(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager("my workspace")
        assert ws.name == "my_workspace"

    def test_empty_name_becomes_default(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        ws = WorkspaceManager("")
        assert ws.name == WorkspaceManager.DEFAULT

    def test_default_constant_is_default(self):
        assert WorkspaceManager.DEFAULT == "default"


class TestWorkspaceListAll:
    def test_empty_when_no_workspaces(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        result = WorkspaceManager.list_all()
        assert result == []

    def test_lists_created_workspaces(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        WorkspaceManager.create("alpha")
        WorkspaceManager.create("beta")
        result = WorkspaceManager.list_all()
        assert "alpha" in result
        assert "beta" in result

    def test_sorted_alphabetically(self, tmp_path, monkeypatch):
        monkeypatch.setattr("agent.workspace.settings.workspace_dir", tmp_path)
        WorkspaceManager.create("zzz")
        WorkspaceManager.create("aaa")
        result = WorkspaceManager.list_all()
        assert result == sorted(result)
