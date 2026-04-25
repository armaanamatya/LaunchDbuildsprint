from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator

from .models import GraphEvent


class EventBus:
    def __init__(self) -> None:
        self._connections: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._connections.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._connections.discard(queue)

    async def publish(self, event: GraphEvent) -> None:
        message = f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
        async with self._lock:
            stale_queues: set[asyncio.Queue[str]] = set()
            for queue in self._connections:
                if queue.full():
                    stale_queues.add(queue)
                    continue
                with contextlib.suppress(RuntimeError, ValueError):
                    queue.put_nowait(message)
            for queue in stale_queues:
                self._connections.discard(queue)

    def reset_for_tests(self) -> None:
        """Drop all queue subscribers. Test-only."""
        self._connections.clear()


async def sse_stream(queue: asyncio.Queue[str]) -> AsyncGenerator[str, None]:
    try:
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=10)
                yield message
            except TimeoutError:
                heartbeat = GraphEvent(type="heartbeat")
                yield f"event: heartbeat\ndata: {json.dumps(heartbeat.model_dump(mode='json'))}\n\n"
    except asyncio.CancelledError:
        raise


event_bus = EventBus()
