"""In-memory realtime hub for dataset collaboration."""

from __future__ import annotations

import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class DatasetHub:
    """Manage WebSocket connections per dataset and broadcast updates."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, dataset_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms.setdefault(dataset_id, set()).add(websocket)

    async def disconnect(self, dataset_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._rooms.get(dataset_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self._rooms.pop(dataset_id, None)

    async def broadcast(self, dataset_id: int, message: dict) -> None:
        dead: Set[WebSocket] = set()
        async with self._lock:
            for ws in self._rooms.get(dataset_id, set()):
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            if dead:
                room = self._rooms.get(dataset_id)
                if room is not None:
                    room.difference_update(dead)
                    if not room:
                        self._rooms.pop(dataset_id, None)


hub = DatasetHub()
