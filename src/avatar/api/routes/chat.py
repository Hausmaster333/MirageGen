# === Файл: src/avatar/api/routes/chat.py ===
"""POST /api/v1/chat endpoint (non-streaming).

Обработка chat-запроса и возврат полного результата (текст + аудио + анимация).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from avatar.schemas.api_types import ChatRequest, ChatResponse

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


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    pipeline: AvatarPipeline = _pipeline_dep,
) -> ChatResponse:
    """POST /api/v1/chat - генерация аватар-ответа (non-streaming).

    Args:
        request: ChatRequest с сообщением пользователя.
        pipeline: Dependency injection AvatarPipeline.

    Returns:
        ChatResponse: Полный ответ с текстом/аудио/анимацией.

    Raises:
        HTTPException: Если обработка завершилась ошибкой.
    """
    raise NotImplementedError("TODO: Implement chat_endpoint")
