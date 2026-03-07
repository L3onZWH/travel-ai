"""Integration tests: TravelAgent + MemoryManager (LLM mocked)."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from agent.core import TravelAgent


@pytest.fixture()
def agent(tmp_workspace, mock_llm):
    with patch("agent.core.AnthropicLLM", return_value=mock_llm):
        return TravelAgent(workspace=tmp_workspace)


class TestAgentMessagePersistence:
    def test_chat_saves_user_message(self, agent):
        agent.chat("我想去东京")
        msgs = agent._memory.get_messages()
        assert any(m["role"] == "user" and "东京" in m["content"] for m in msgs)

    def test_chat_saves_assistant_response(self, agent):
        agent.chat("你好")
        msgs = agent._memory.get_messages()
        assert any(m["role"] == "assistant" for m in msgs)

    def test_history_written_to_disk(self, agent):
        agent.chat("测试消息")
        history_path = agent._memory._history_path
        assert history_path.exists()
        data = json.loads(history_path.read_text())
        assert len(data) >= 2  # user + assistant

    def test_conversation_md_written(self, agent):
        agent.chat("测试")
        assert agent._memory._conv_path.exists()

    def test_clear_history_resets(self, agent):
        agent.chat("你好")
        agent.clear_history()
        assert agent._memory.get_messages() == []


class TestAgentSessionReload:
    def test_reload_restores_history(self, tmp_workspace, mock_llm):
        """Create agent, add messages, reload with same session_id → history intact."""
        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            agent1 = TravelAgent(session_id="reload_test", workspace=tmp_workspace)
        agent1.chat("第一条消息")

        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            agent2 = TravelAgent(session_id="reload_test", workspace=tmp_workspace)

        msgs = agent2._memory.get_messages()
        assert any("第一条消息" in str(m) for m in msgs)

    def test_different_sessions_are_isolated(self, tmp_workspace, mock_llm):
        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            a1 = TravelAgent(session_id="ses_a", workspace=tmp_workspace)
            a2 = TravelAgent(session_id="ses_b", workspace=tmp_workspace)

        a1.chat("session A message")
        assert a2._memory.get_messages() == []


class TestAgentSystemPrompt:
    def test_rules_injected_when_rule_file_exists(self, tmp_workspace, mock_llm, tmp_path):
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("每次回复需包含费用估算", encoding="utf-8")

        from agent.rules import RulesEngine
        engine = RulesEngine(rules_path=rule_file)

        with patch("agent.core.AnthropicLLM", return_value=mock_llm):
            agent = TravelAgent(workspace=tmp_workspace)
        agent._rules = engine

        system = agent._build_system_prompt()
        assert "费用估算" in system

    def test_system_prompt_always_has_base(self, agent):
        system = agent._build_system_prompt()
        assert "旅行" in system  # SYSTEM_PROMPT mentions travel


class TestAgentProfile:
    def test_update_profile_persists(self, agent):
        agent.update_profile({"preferred_language": "zh"})
        profile = agent._memory.load_profile()
        assert profile["preferred_language"] == "zh"
