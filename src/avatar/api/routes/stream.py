"""WebSocket /api/v1/stream endpoint (streaming)."""

from __future__ import annotations

import base64
import contextlib
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from loguru import logger

from avatar.api.dependencies import get_pipeline  # <-- импорт из dependencies

if TYPE_CHECKING:
    from avatar.pipeline.avatar_pipeline import AvatarPipeline

router = APIRouter()


@router.websocket("/stream")
async def stream_endpoint(
    websocket: WebSocket,
    pipeline: AvatarPipeline = Depends(get_pipeline),  # noqa: B008
) -> None:
    """WebSocket /api/v1/stream - стриминг аватар-ответа."""
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") != "chat":
                await websocket.send_json({"type": "error", "message": "Invalid message type"})
                continue

            message = data.get("message", "")
            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            logger.info(f"Received message: {message[:50]}...")

            full_text = ""
            total_duration = 0.0

            async for frame in pipeline.process(user_input=message):
                payload: dict[str, Any] = {
                    "type": "frame",
                    "timestamp": frame.timestamp,
                }

                if frame.text_chunk:
                    payload["text_chunk"] = frame.text_chunk
                    full_text += frame.text_chunk

                if frame.audio_chunk:
                    payload["audio_chunk"] = base64.b64encode(frame.audio_chunk).decode("utf-8")

                if frame.blendshapes:
                    payload["blendshapes"] = frame.blendshapes

                if frame.motion:
                    payload["motion"] = {bone: list(quat) for bone, quat in frame.motion.items()}

                total_duration = frame.timestamp
                await websocket.send_json(payload)

            await websocket.send_json({
                "type": "done",
                "full_text": full_text,
                "total_duration": total_duration,
            })

            logger.info(f"Streaming completed: {total_duration:.2f}s")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "error", "message": str(e)})
