from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncGenerator, Callable

from .models import GraphEvent

logger = logging.getLogger(__name__)

EventFilter = Callable[[GraphEvent], bool]


class EventBus:
    """Async fan-out pub/sub with optional per-subscriber predicate filtering.

    The previous per-node SSE filter substring-matched ``"node_id": "..."`` in
    the serialized JSON, which produced false positives when a node id appeared
    inside another field. ``subscribe(predicate=...)`` now does the filtering at
    the bus level against the typed event, before serialization.
    """

    def __init__(self) -> None:
        self._connections: set[asyncio.Queue[str]] = set()
        self._predicates: dict[asyncio.Queue[str], EventFilter] = {}
        self._dropped: dict[asyncio.Queue[str], int] = {}
        self._lock = asyncio.Lock()

    async def subscribe(
        self,
        *,
        predicate: EventFilter | None = None,
    ) -> asyncio.Queue[str]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=200)
        async with self._lock:
            self._connections.add(queue)
            if predicate is not None:
                self._predicates[queue] = predicate
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[str]) -> None:
        async with self._lock:
            self._connections.discard(queue)
            self._predicates.pop(queue, None)
            self._dropped.pop(queue, None)

    async def publish(self, event: GraphEvent) -> None:
        message = f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
        async with self._lock:
            stale_queues: set[asyncio.Queue[str]] = set()
            for queue in self._connections:
                predicate = self._predicates.get(queue)
                if predicate is not None and not predicate(event):
                    continue
                if queue.full():
                    count = self._dropped.get(queue, 0) + 1
                    self._dropped[queue] = count
                    if count == 1 or count % 25 == 0:
                        logger.warning(
                            "event_subscriber_overflow dropped=%d (queue full).",
                            count,
                        )
                    stale_queues.add(queue)
                    continue
                with contextlib.suppress(RuntimeError, ValueError):
                    queue.put_nowait(message)
            for queue in stale_queues:
                self._connections.discard(queue)
                self._predicates.pop(queue, None)

    def reset_for_tests(self) -> None:
        """Drop all queue subscribers. Test-only."""
        self._connections.clear()
        self._predicates.clear()
        self._dropped.clear()


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
