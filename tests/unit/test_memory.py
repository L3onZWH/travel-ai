"""Unit tests for memory/manager.py."""
from __future__ import annotations

import json


class TestMemoryMessages:
    def test_add_and_get_messages(self, tmp_memory):
        tmp_memory.add_message("user", "你好")
        tmp_memory.add_message("assistant", "你好！")
        msgs = tmp_memory.get_messages()
        assert len(msgs) == 2
        assert msgs[0] == {"role": "user", "content": "你好"}
        assert msgs[1] == {"role": "assistant", "content": "你好！"}

    def test_history_json_written_to_disk(self, tmp_memory):
        tmp_memory.add_message("user", "test")
        assert tmp_memory._history_path.exists()
        data = json.loads(tmp_memory._history_path.read_text())
        assert data[0]["content"] == "test"

    def test_get_messages_with_window(self, tmp_memory):
        for i in range(5):
            tmp_memory.add_message("user", f"msg {i}")
        result = tmp_memory.get_messages(window=2)
        assert len(result) == 2
        assert result[-1]["content"] == "msg 4"

    def test_clear_history(self, tmp_memory):
        tmp_memory.add_message("user", "hello")
        tmp_memory.clear_history()
        assert tmp_memory.get_messages() == []
        data = json.loads(tmp_memory._history_path.read_text())
        assert data == []

    def test_clear_removes_conversation_md(self, tmp_memory):
        tmp_memory.add_message("user", "hello")
        assert tmp_memory._conv_path.exists()
        tmp_memory.clear_history()
        assert not tmp_memory._conv_path.exists()


class TestConversationMd:
    def test_conversation_md_created_on_first_message(self, tmp_memory):
        assert not tmp_memory._conv_path.exists()
        tmp_memory.add_message("user", "first message")
        assert tmp_memory._conv_path.exists()

    def test_conversation_md_contains_user_message(self, tmp_memory):
        tmp_memory.add_message("user", "去东京旅行")
        content = tmp_memory._conv_path.read_text(encoding="utf-8")
        assert "去东京旅行" in content

    def test_conversation_md_contains_assistant_message(self, tmp_memory):
        tmp_memory.add_message("assistant", "东京很美！")
        content = tmp_memory._conv_path.read_text(encoding="utf-8")
        assert "东京很美！" in content

    def test_conversation_md_has_header(self, tmp_memory):
        tmp_memory.add_message("user", "hi")
        content = tmp_memory._conv_path.read_text(encoding="utf-8")
        assert "## 对话记录" in content

    def test_list_content_not_written_to_md(self, tmp_memory):
        """Non-string content (tool_use blocks) should NOT be written to MD."""
        tmp_memory.add_message("assistant", [{"type": "tool_use", "id": "t1"}])
        assert not tmp_memory._conv_path.exists()


class TestMeta:
    def test_meta_json_created_on_init(self, tmp_memory):
        assert tmp_memory._meta_path.exists()

    def test_meta_contains_session_id(self, tmp_memory):
        meta = json.loads(tmp_memory._meta_path.read_text())
        assert meta["session_id"] == "ses_test"

    def test_set_title_updates_meta(self, tmp_memory):
        tmp_memory.set_title("Tokyo Trip")
        meta = json.loads(tmp_memory._meta_path.read_text())
        assert meta["title"] == "Tokyo Trip"


class TestUserProfile:
    def test_load_profile_empty_initially(self, tmp_memory):
        assert tmp_memory.load_profile() == {}

    def test_save_and_load_profile(self, tmp_memory):
        tmp_memory.save_profile({"language": "zh", "budget": 10000})
        profile = tmp_memory.load_profile()
        assert profile["language"] == "zh"
        assert profile["budget"] == 10000

    def test_update_profile_merges(self, tmp_memory):
        tmp_memory.save_profile({"a": 1})
        tmp_memory.update_profile({"b": 2})
        profile = tmp_memory.load_profile()
        assert profile["a"] == 1
        assert profile["b"] == 2
