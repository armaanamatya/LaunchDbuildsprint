from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    demo_repo_path: str | None = Field(default=None, alias="AGENT_GRAPH_DEMO_REPO_PATH")
    base_branch: str = Field(default="main", alias="AGENT_GRAPH_BASE_BRANCH")
    demo_baseline_ref: str = Field(
        default="refs/agent-graph/demo-baseline",
        alias="AGENT_GRAPH_DEMO_BASELINE_REF",
    )
    worktree_dir: str = Field(default=".agent-worktrees", alias="AGENT_GRAPH_WORKTREE_DIR")
    enable_real_runs: bool = Field(default=False, alias="AGENT_GRAPH_ENABLE_REAL_RUNS")
    enable_eval: bool = Field(default=True, alias="AGENT_GRAPH_ENABLE_EVAL")
    host: str = Field(default="127.0.0.1", alias="AGENT_GRAPH_HOST")
    port: int = Field(default=8000, alias="AGENT_GRAPH_PORT")
    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173",
        alias="AGENT_GRAPH_CORS_ORIGINS",
    )

    @property
    def resolved_demo_repo_path(self) -> str | None:
        if self.demo_repo_path:
            return str(Path(self.demo_repo_path).resolve())

        default_demo_repo = Path(__file__).resolve().parents[2] / "demo-repo"
        if default_demo_repo.exists():
            return str(default_demo_repo)

        return None

    @property
    def worktree_root(self) -> str:
        repo_path = Path(self.resolved_demo_repo_path) if self.resolved_demo_repo_path else Path.cwd().parent
        return str(repo_path / self.worktree_dir)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
