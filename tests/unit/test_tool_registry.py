"""Unit tests for tools/registry.py."""
from __future__ import annotations

from tools.base import BaseTool, ToolResult
from tools.registry import ToolRegistry


class FakeTool(BaseTool):
    name = "fake_tool"
    description = "A fake tool for testing."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def execute(self, query: str = "") -> ToolResult:  # type: ignore[override]
        return ToolResult(success=True, data=f"result:{query}")


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = FakeTool()
        reg.register(tool)
        assert reg.get("fake_tool") is tool

    def test_get_unknown_returns_none(self):
        reg = ToolRegistry()
        assert reg.get("no_such_tool") is None

    def test_all_tools_returns_registered(self):
        reg = ToolRegistry()
        reg.register(FakeTool())
        assert len(reg.all_tools()) == 1

    def test_to_claude_schemas_structure(self):
        reg = ToolRegistry()
        reg.register(FakeTool())
        schemas = reg.to_claude_schemas()
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["name"] == "fake_tool"
        assert "description" in schema
        assert "input_schema" in schema

    def test_to_claude_schema_alias(self):
        """to_claude_schema() must be an alias for to_claude_schemas()."""
        reg = ToolRegistry()
        reg.register(FakeTool())
        assert reg.to_claude_schema() == reg.to_claude_schemas()

    def test_execute_known_tool(self):
        reg = ToolRegistry()
        reg.register(FakeTool())
        result = reg.execute("fake_tool", query="tokyo")
        assert result.success is True
        assert "tokyo" in result.data

    def test_execute_unknown_tool_returns_error(self):
        reg = ToolRegistry()
        result = reg.execute("ghost_tool")
        assert result.success is False
        assert "Unknown tool" in result.data

    def test_execute_catches_exceptions(self):
        class BrokenTool(BaseTool):
            name = "broken"
            description = "breaks"
            parameters = {"type": "object", "properties": {}}

            def execute(self, **kwargs) -> ToolResult:
                raise RuntimeError("boom")

        reg = ToolRegistry()
        reg.register(BrokenTool())
        result = reg.execute("broken")
        assert result.success is False
        assert "boom" in result.data
