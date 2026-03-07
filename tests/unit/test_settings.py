"""Unit tests for config/settings.py."""
from __future__ import annotations

from config.settings import BASE_DIR, settings


class TestSettingsPaths:
    def test_base_dir_is_project_root(self):
        assert (BASE_DIR / "pyproject.toml").exists()

    def test_memory_dir_under_workspace(self):
        assert settings.memory_dir == settings.workspace_dir / "memory"

    def test_sessions_dir_under_workspace(self):
        assert settings.sessions_dir == settings.workspace_dir / "sessions"

    def test_knowledge_dir_under_workspace(self):
        assert settings.knowledge_dir == settings.workspace_dir / "knowledge"

    def test_rules_file_in_config(self):
        assert settings.rules_file.parent.name == "config"
        assert settings.rules_file.name == "rule.md"

    def test_soul_file_in_config(self):
        assert settings.soul_file.parent.name == "config"
        assert settings.soul_file.name == "soul.md"


class TestEnsureDirs:
    def test_ensure_dirs_creates_workspace(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "workspace_dir", tmp_path / "ws")
        ws = tmp_path / "ws"
        ws.mkdir(parents=True, exist_ok=True)
        mem = ws / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        ses = ws / "sessions"
        ses.mkdir(parents=True, exist_ok=True)
        assert ws.is_dir()
        assert mem.is_dir()
        assert ses.is_dir()
