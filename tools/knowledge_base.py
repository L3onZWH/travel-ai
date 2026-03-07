from __future__ import annotations

from pathlib import Path

from config.settings import settings
from tools.base import BaseTool, ToolResult


class KnowledgeBaseTool(BaseTool):
    """Read / write destination knowledge stored in context/knowledge/."""

    name = "knowledge_base"
    description = (
        "Access the local knowledge base of curated travel information. "
        "Supports 'read' (retrieve a destination's info) and "
        "'write' (save new info for a destination)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "write", "list"],
                "description": (  # noqa: E501
                    "'read' returns stored info; 'write' saves it; 'list' shows all destinations."
                ),
            },
            "destination": {
                "type": "string",
                "description": "Destination name (used as filename, e.g. 'tokyo').",
            },
            "content": {
                "type": "string",
                "description": "Markdown content to save (required for 'write').",
            },
        },
        "required": ["action"],
    }

    def __init__(self) -> None:
        self._kb_dir: Path = settings.knowledge_dir / "destinations"
        self._kb_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    def execute(  # type: ignore[override]
        self,
        action: str,
        destination: str = "",
        content: str = "",
    ) -> ToolResult:
        if action == "list":
            return self._list()
        if action == "read":
            return self._read(destination)
        if action == "write":
            return self._write(destination, content)
        return ToolResult(success=False, data=f"Unknown action: {action}")

    # ------------------------------------------------------------------ #
    def _list(self) -> ToolResult:
        files = sorted(self._kb_dir.glob("*.md"))
        if not files:
            return ToolResult(success=True, data="Knowledge base is empty.")
        names = [f.stem for f in files]
        return ToolResult(
            success=True,
            data="Available destinations:\n" + "\n".join(f"  - {n}" for n in names),
            raw={"destinations": names},
        )

    def _read(self, destination: str) -> ToolResult:
        if not destination:
            return ToolResult(success=False, data="'destination' is required for read.")
        path = self._kb_dir / f"{destination.lower()}.md"
        if not path.exists():
            return ToolResult(
                success=False,
                data=f"No knowledge found for '{destination}'. Try web_search instead.",
            )
        return ToolResult(success=True, data=path.read_text(encoding="utf-8"))

    def _write(self, destination: str, content: str) -> ToolResult:
        if not destination or not content:
            return ToolResult(
                success=False,
                data="Both 'destination' and 'content' are required for write.",
            )
        path = self._kb_dir / f"{destination.lower()}.md"
        path.write_text(content, encoding="utf-8")
        return ToolResult(
            success=True,
            data=f"Saved knowledge for '{destination}' → {path}",
        )
