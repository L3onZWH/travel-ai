"""
Smoke tests — require a real ANTHROPIC_API_KEY.

Run with:
    pytest tests/smoke/ -v -m smoke

Skipped automatically when ANTHROPIC_API_KEY is not set.
"""

from __future__ import annotations

import pytest

from config.settings import settings

# Skip entire module if no API key
pytestmark = pytest.mark.smoke


@pytest.fixture(autouse=True)
def require_api_key():
    if not settings.anthropic_api_key or settings.anthropic_api_key.startswith("sk-ant-..."):
        pytest.skip("ANTHROPIC_API_KEY not configured — skipping smoke tests")


class TestApiConnection:
    def test_llm_returns_non_empty_response(self, tmp_workspace):
        """Fire one real API call and check we get text back."""
        from llm.anthropic_llm import AnthropicLLM
        from tools.registry import ToolRegistry

        llm = AnthropicLLM(tool_registry=ToolRegistry())
        response = llm.chat(
            system="你是一个助手，请用中文简短回答。",
            messages=[{"role": "user", "content": "你好"}],
        )
        assert isinstance(response, str)
        assert len(response) > 0

    def test_travel_question_answered(self, tmp_workspace):
        """Ask a travel question and verify the response is substantive."""
        from agent.core import TravelAgent

        agent = TravelAgent(workspace=tmp_workspace)
        response = agent.chat("北京有什么著名景点？只兩3个。")
        assert isinstance(response, str)
        assert len(response) > 20

    def test_stream_yields_chunks(self, tmp_workspace):
        """Streaming should yield at least one chunk."""
        from agent.core import TravelAgent

        agent = TravelAgent(workspace=tmp_workspace)
        chunks = list(agent.stream("用一句话介绍东京。"))
        full = "".join(chunks)
        assert len(full) > 0
