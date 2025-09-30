"""WebSocket endpoints for realtime dataset collaboration."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .realtime import hub

ws_router = APIRouter()


@ws_router.websocket('/ws/datasets/{dataset_id}')
async def dataset_ws(websocket: WebSocket, dataset_id: int) -> None:
    await hub.connect(dataset_id, websocket)
    try:
        while True:
            # We only keep the connection alive; edits flow through REST then broadcast.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(dataset_id, websocket)
