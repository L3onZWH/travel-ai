"""Unit tests for tools/knowledge_base.py."""
from __future__ import annotations

import pytest

from tools.knowledge_base import KnowledgeBaseTool


@pytest.fixture()
def kb(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.knowledge_base.settings.knowledge_dir", tmp_path)
    return KnowledgeBaseTool()


class TestKnowledgeBase:
    def test_read_missing_destination_fails(self, kb):
        result = kb.execute(action="read", destination="nowhere")
        assert result.success is False
        assert "nowhere" in result.data

    def test_write_then_read(self, kb):
        write_result = kb.execute(
            action="write",
            destination="tokyo",
            content="# Tokyo\n东京是日本的首都。",
        )
        assert write_result.success is True

        read_result = kb.execute(action="read", destination="tokyo")
        assert read_result.success is True
        assert "东京是日本的首都" in read_result.data

    def test_list_empty(self, kb):
        result = kb.execute(action="list")
        assert result.success is True
        assert "empty" in result.data.lower() or "为空" in result.data

    def test_list_with_destinations(self, kb):
        kb.execute(action="write", destination="tokyo", content="Tokyo info")
        kb.execute(action="write", destination="paris", content="Paris info")
        result = kb.execute(action="list")
        assert result.success is True
        assert "tokyo" in result.data
        assert "paris" in result.data

    def test_write_requires_destination(self, kb):
        result = kb.execute(action="write", destination="", content="some content")
        assert result.success is False

    def test_write_requires_content(self, kb):
        result = kb.execute(action="write", destination="tokyo", content="")
        assert result.success is False

    def test_read_requires_destination(self, kb):
        result = kb.execute(action="read", destination="")
        assert result.success is False

    def test_unknown_action_fails(self, kb):
        result = kb.execute(action="delete", destination="tokyo")
        assert result.success is False
