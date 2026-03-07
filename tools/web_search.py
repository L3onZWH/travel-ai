from __future__ import annotations

from typing import Any

try:
    from ddgs import DDGS  # pip install ddgs
    _DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS  # fallback
        _DDGS_AVAILABLE = True
    except ImportError:
        _DDGS_AVAILABLE = False

from config.settings import settings
from tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the internet for up-to-date travel information such as visa "
        "requirements, local tips, attractions, weather, events, and prices. "
        "Use this when your internal knowledge might be outdated."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string (in English or Chinese).",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return (default 5).",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def execute(self, query: str, max_results: int = 5) -> ToolResult:  # type: ignore[override]
        if not _DDGS_AVAILABLE:
            return ToolResult(
                success=False,
                data="ddgs is not installed. Run: pip install ddgs",
            )

        max_results = min(max_results, settings.search_max_results)
        try:
            with DDGS() as ddgs:
                results: list[dict[str, Any]] = list(
                    ddgs.text(query, max_results=max_results)
                )
            if not results:
                return ToolResult(success=True, data="No results found.", raw={})

            formatted = "\n\n".join(
                f"[{i + 1}] {r.get('title', 'No title')}\n"
                f"URL: {r.get('href', '')}\n"
                f"{r.get('body', '')}"
                for i, r in enumerate(results)
            )
            return ToolResult(success=True, data=formatted, raw={"results": results})
        except Exception as exc:  # noqa: BLE001
            return ToolResult(success=False, data=f"Search failed: {exc}")
