from __future__ import annotations

from tools.base import BaseTool, ToolResult


class ToolRegistry:
    """Central registry that maps tool names to BaseTool instances."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    # ------------------------------------------------------------------ #
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def to_claude_schemas(self) -> list[dict]:
        return [t.to_claude_schema() for t in self._tools.values()]

    def to_claude_schema(self) -> list[dict]:
        """Alias for to_claude_schemas (backward compat)."""
        return self.to_claude_schemas()

    # ------------------------------------------------------------------ #
    def execute(self, name: str, **kwargs) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                data=f"Unknown tool: {name}",
            )
        try:
            return tool.execute(**kwargs)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                success=False,
                data=f"Tool '{name}' raised an error: {exc}",
            )
