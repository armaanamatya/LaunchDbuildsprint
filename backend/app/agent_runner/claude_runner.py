from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from .base import AgentRunner, NormalizedEvent
from .prompts import CODING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClaudeAgentRunner(AgentRunner):
    """Runs a real Claude agent via the claude-agent-sdk."""

    async def stream(
        self,
        node_id: str,
        prompt: str,
        worktree_path: str,
    ) -> AsyncGenerator[NormalizedEvent, None]:
        try:
            from claude_agent_sdk import (
                ClaudeAgentOptions,
                AssistantMessage,
                ResultMessage,
                TextBlock,
                ToolUseBlock,
                ToolResultBlock,
                query,
            )
        except ImportError as exc:
            yield NormalizedEvent(
                type="agent_failed",
                node_id=node_id,
                content="claude-agent-sdk is not installed. Run: uv add claude-agent-sdk",
                is_error=True,
            )
            logger.error("claude-agent-sdk not installed: %s", exc)
            return

        yield NormalizedEvent(type="agent_started", node_id=node_id)

        options = ClaudeAgentOptions(
            cwd=Path(worktree_path),
            system_prompt=CODING_SYSTEM_PROMPT,
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "LS"],
            permission_mode="acceptEdits",
        )

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            if block.text.strip():
                                yield NormalizedEvent(
                                    type="agent_text",
                                    node_id=node_id,
                                    content=block.text,
                                )
                        elif isinstance(block, ToolUseBlock):
                            yield NormalizedEvent(
                                type="agent_tool_use",
                                node_id=node_id,
                                tool_name=block.name,
                                tool_input=block.input,
                            )
                        elif isinstance(block, ToolResultBlock):
                            is_err = bool(block.is_error)
                            content = block.content if isinstance(block.content, str) else str(block.content)
                            yield NormalizedEvent(
                                type="agent_tool_result",
                                node_id=node_id,
                                content=content[:500] if content else None,
                                is_error=is_err,
                            )

                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        yield NormalizedEvent(
                            type="agent_failed",
                            node_id=node_id,
                            content=message.result or "Agent run ended with an error.",
                            is_error=True,
                        )
                    else:
                        yield NormalizedEvent(
                            type="agent_completed",
                            node_id=node_id,
                            content=message.result or "Agent run completed.",
                        )

        except Exception as exc:
            logger.error("ClaudeAgentRunner error for node %s: %s", node_id, exc, exc_info=True)
            yield NormalizedEvent(
                type="agent_failed",
                node_id=node_id,
                content=str(exc),
                is_error=True,
            )
