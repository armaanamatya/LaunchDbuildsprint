from __future__ import annotations

from .base import AgentRunner, NormalizedEvent
from .claude_runner import ClaudeAgentRunner
from .mock_runner import MockAgentRunner
from ..settings import get_settings


def get_runner() -> AgentRunner:
    """Return the appropriate runner based on settings."""
    if get_settings().enable_real_runs:
        return ClaudeAgentRunner()
    return MockAgentRunner()


__all__ = ["AgentRunner", "NormalizedEvent", "ClaudeAgentRunner", "MockAgentRunner", "get_runner"]
