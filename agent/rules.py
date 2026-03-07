from __future__ import annotations

from pathlib import Path

from config.settings import settings


class RulesEngine:
    """
    加载 rule.md（硬性规则）和 soul.md（感性偏好）并注入 system prompt。
    每次对话循环都重新读文件，支持热重载。
    """

    def __init__(
        self,
        rules_path: Path | None = None,
        soul_path: Path | None = None,
    ) -> None:
        self._rules_path: Path = rules_path or settings.rules_file
        self._soul_path: Path = soul_path or settings.soul_file

    def _read(self, path: Path) -> str:
        """Return file text, empty string if missing."""
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
        return ""

    def load(self) -> str:
        """Return the raw text of rule.md (empty string if missing)."""
        return self._read(self._rules_path)

    def load_soul(self) -> str:
        """Return the raw text of soul.md (empty string if missing)."""
        return self._read(self._soul_path)

    def as_system_block(self) -> str:
        """Combine rule.md + soul.md into a labelled system prompt block."""
        parts: list[str] = []

        rules = self.load()
        if rules:
            parts.append(f"## 行为规则 (rule.md)\n\n{rules}")

        soul = self.load_soul()
        if soul:
            parts.append(f"## 用户偏好 (soul.md)\n\n{soul}")

        if not parts:
            return ""
        return "\n\n".join(parts) + "\n\n---"

