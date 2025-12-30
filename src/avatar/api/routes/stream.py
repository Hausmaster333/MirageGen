# === Файл: src/avatar/api/routes/stream.py ===
"""WebSocket /api/v1/stream endpoint (streaming).

Стриминг AvatarFrame через WebSocket (текст → аудио → blendshapes → motion).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, WebSocket

if TYPE_CHECKING:
    from avatar.pipeline.avatar_pipeline import AvatarPipeline

router = APIRouter()


def get_pipeline() -> AvatarPipeline:
    """Dependency injection для AvatarPipeline.

    Returns:
        AvatarPipeline: Инстанс пайплайна.

    Raises:
        RuntimeError: Если пайплайн не инициализирован.
    """
    raise NotImplementedError("TODO: Implement get_pipeline dependency")


_pipeline_dep = Depends(get_pipeline)


@router.websocket("/stream")
async def stream_endpoint(
    websocket: WebSocket,
    pipeline: AvatarPipeline = _pipeline_dep,
) -> None:
    """WebSocket /api/v1/stream - стриминг аватар-ответа.

    Args:
        websocket: WebSocket соединение.
        pipeline: Dependency injection AvatarPipeline.

    Raises:
        WebSocketDisconnect: Если клиент отключился.
    """
    raise NotImplementedError("TODO: Implement stream_endpoint")
