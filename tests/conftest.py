"""Shared pytest fixtures for all test levels."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent.workspace import WorkspaceManager
from memory.manager import MemoryManager

# ─────────────────────────────────────────────────────────────────────────── #
# Workspace / path fixtures                                                   #
# ─────────────────────────────────────────────────────────────────────────── #


@pytest.fixture()
def tmp_workspace(tmp_path: Path) -> WorkspaceManager:
    """An isolated WorkspaceManager rooted in pytest's tmp_path."""
    ws = WorkspaceManager.__new__(WorkspaceManager)
    ws.name = "test"
    ws._root = tmp_path / "ws" / "test"
    ws.ensure_dirs()
    return ws


@pytest.fixture()
def tmp_memory(tmp_workspace: WorkspaceManager) -> MemoryManager:
    """A MemoryManager backed by tmp_workspace."""
    return MemoryManager(session_id="ses_test", workspace=tmp_workspace)


# ─────────────────────────────────────────────────────────────────────────── #
# LLM mocks                                                                   #
# ─────────────────────────────────────────────────────────────────────────── #


@pytest.fixture()
def mock_llm() -> MagicMock:
    """LLM that immediately returns a deterministic reply."""
    llm = MagicMock()
    llm.chat.return_value = "这是测试回复。"
    llm.stream.return_value = iter(["这是", "测试", "回复。"])
    return llm


# ─────────────────────────────────────────────────────────────────────────── #
# Agent fixture (LLM mocked, real memory + workspace)                         #
# ─────────────────────────────────────────────────────────────────────────── #


@pytest.fixture()
def travel_agent(tmp_workspace: WorkspaceManager, mock_llm: MagicMock):
    """TravelAgent with mocked LLM and isolated workspace."""
    from agent.core import TravelAgent

    with patch("agent.core.AnthropicLLM", return_value=mock_llm):
        agent = TravelAgent(workspace=tmp_workspace)
    return agent
