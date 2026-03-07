from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Anthropic ──────────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(default="", alias="ANTHROPIC_BASE_URL")
    anthropic_model: str = Field(default="claude-opus-4-5", alias="ANTHROPIC_MODEL")

    # ── Paths ───────────────────────────────────────────────────────────────────────
    base_dir: Path = BASE_DIR
    workspace_dir: Path = BASE_DIR / "workspace"
    knowledge_dir: Path = BASE_DIR / "workspace" / "knowledge"
    config_dir: Path = BASE_DIR / "config"

    # rules / soul / model config files (inside config/)
    rules_file: Path = BASE_DIR / "config" / "rule.md"
    soul_file: Path = BASE_DIR / "config" / "soul.md"
    model_file: Path = BASE_DIR / "config" / "model.md"

    # memory lives under workspace/
    @property
    def memory_dir(self) -> Path:
        return self.workspace_dir / "memory"

    # sessions live under workspace/sessions/
    @property
    def sessions_dir(self) -> Path:
        return self.workspace_dir / "sessions"

    # ── LLM params ─────────────────────────────────────────────────────────────────
    max_tokens: int = Field(default=4096)
    max_tool_iterations: int = Field(default=5)

    # ── Search ─────────────────────────────────────────────────────────────────
    search_max_results: int = Field(default=5)
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    def ensure_dirs(self) -> None:
        """Create runtime directories if they don't exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        (self.knowledge_dir / "destinations").mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
