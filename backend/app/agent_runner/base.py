from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any, Literal

NormalizedEventType = Literal[
    "agent_started",
    "agent_text",
    "agent_tool_use",
    "agent_tool_result",
    "agent_completed",
    "agent_failed",
]

# Mirrors NodeStrategy in models.py. Kept as a plain literal here to avoid a
# cyclic import between the runner layer and the public model contracts.
StrategyHint = Literal["route_local", "dependency", "middleware"]


@dataclass
class NormalizedEvent:
    type: NormalizedEventType
    node_id: str
    content: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] = field(default_factory=dict)
    is_error: bool = False


class AgentRunner(ABC):
    """Abstract base for agent runners. Subclasses implement stream()."""

    @abstractmethod
    async def stream(
        self,
        node_id: str,
        prompt: str,
        worktree_path: str,
        strategy: StrategyHint | None = None,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        """Yield NormalizedEvents for the full agent run lifecycle.

        ``strategy`` biases the implementation approach (route_local /
        dependency / middleware). Concrete runners may use it to pick a
        canned implementation (mock) or to bias the system prompt (Claude).
        """
        # Make type checkers happy; concrete implementations use `yield` directly.
        raise NotImplementedError
        yield  # pragma: no cover
