"""Pydantic-модели для API запросов/ответов.

Используются в REST/WebSocket эндпоинтах, как это задано в SPEC.md.
"""

from pydantic import BaseModel, Field

from avatar.schemas.animation_types import BlendshapeWeights, MotionKeyframes
from avatar.schemas.audio_types import AudioSegment
from avatar.schemas.llm_types import Message


class ChatRequest(BaseModel):
    """Запрос для POST /api/v1/chat (non-streaming).

    Attributes:
        message: Текст сообщения пользователя.
        conversation_history: Опциональная история диалога.
    """

    message: str = Field(..., min_length=1, max_length=2000, description="User message text.")
    conversation_history: list[Message] | None = Field(
        default=None,
        description="Optional conversation history.",
    )


class AvatarFrame(BaseModel):
    """Один фрейм стриминга для WebSocket (может содержать текст/аудио/blendshapes/motion).

    Attributes:
        timestamp: Время фрейма в секундах от начала стрима.
        text_chunk: Опциональный текстовый чанк (генерация LLM).
        audio_chunk: Опциональные байты аудио-чанка.
        blendshapes: Опциональные веса blendshape для этого кадра.
        motion: Опциональные кватернионы костей (bone -> (x,y,z,w)).
    """

    timestamp: float = Field(..., ge=0.0, description="Frame timestamp (seconds).")
    text_chunk: str | None = Field(default=None, description="Optional text chunk.")
    audio_chunk: bytes | None = Field(default=None, description="Optional audio chunk bytes.")
    blendshapes: dict[str, float] | None = Field(
        default=None,
        description="Optional blendshape weights.",
    )
    motion: dict[str, tuple[float, float, float, float]] | None = Field(
        default=None,
        description="Optional bone rotations (quaternion).",
    )


class ChatResponse(BaseModel):
    """Ответ для POST /api/v1/chat (non-streaming).

    Attributes:
        full_text: Полный сгенерированный текст ответа.
        audio: Аудио-сегмент TTS.
        blendshapes: Blendshape-анимация для аудио.
        motion: Motion-анимация (жест/эмоция).
        processing_time: Общее время обработки в секундах.
    """

    full_text: str = Field(..., description="Full generated text.")
    audio: AudioSegment = Field(..., description="TTS audio segment.")
    blendshapes: BlendshapeWeights = Field(..., description="Lipsync blendshape weights.")
    motion: MotionKeyframes = Field(..., description="Motion animation keyframes.")
    processing_time: float = Field(..., ge=0.0, description="Total processing time (seconds).")
