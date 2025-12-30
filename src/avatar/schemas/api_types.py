"""Pydantic-модели для API запросов/ответов.

Используются в REST/WebSocket эндпоинтах, как это задано в SPEC.md.
"""

from pydantic import BaseModel, Field, field_validator

from avatar.schemas.animation_types import BlendshapeWeights, MotionKeyframes
from avatar.schemas.llm_types import Message


class ChatRequest(BaseModel):
    """Запрос для POST /api/v1/chat (non-streaming).

    Attributes:
        message: Текст сообщения пользователя (1-2000 символов).
        conversation_history: Опциональная история диалога.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User message text (1-2000 characters).",
    )
    conversation_history: list[Message] | None = Field(
        default=None,
        description="Optional conversation history.",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Валидация сообщения.

        Args:
            v: Текст сообщения.

        Returns:
            str: Валидированное сообщение.

        Raises:
            ValueError: Если сообщение пустое или слишком длинное.
        """
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        if len(v) > 2000:
            raise ValueError(f"message too long: {len(v)} chars (max 2000)")
        return v


class AudioSegmentResponse(BaseModel):
    """Audio segment для API response (с base64-кодированным аудио).

    Используется в ChatResponse для передачи аудио через JSON.
    Для WebSocket стриминга используется AvatarFrame с бинарными байтами.

    Attributes:
        audio_bytes_base64: Base64-кодированные аудио-байты.
        sample_rate: Частота дискретизации (Hz).
        format: Формат аудио ("wav", "mp3").
        duration: Длительность аудио в секундах.
    """

    audio_bytes_base64: str = Field(
        ...,
        description="Base64 encoded audio data (WAV/MP3).",
    )
    sample_rate: int = Field(
        default=48000,
        ge=8000,
        le=48000,
        description="Audio sample rate in Hz.",
    )
    format: str = Field(
        default="wav",
        pattern="^(wav|mp3)$",
        description="Audio format (wav or mp3).",
    )
    duration: float = Field(
        ...,
        ge=0.0,
        description="Audio duration in seconds.",
    )


class AvatarFrame(BaseModel):
    """Один фрейм стриминга для WebSocket (может содержать текст/аудио/blendshapes/motion).

    Используется для потоковой передачи данных через WebSocket /api/v1/stream.
    Каждый фрейм может содержать один или несколько компонентов (текст, аудио, анимацию).

    Attributes:
        timestamp: Время фрейма в секундах от начала стрима.
        text_chunk: Опциональный текстовый чанк (генерация LLM).
        audio_chunk: Опциональные байты аудио-чанка (бинарные WAV данные).
        blendshapes: Опциональные веса blendshape для этого кадра (viseme веса для губ).
        motion: Опциональные кватернионы костей (bone_name -> (x, y, z, w)).
    """

    timestamp: float = Field(
        ...,
        ge=0.0,
        description="Frame timestamp in seconds from stream start.",
    )
    text_chunk: str | None = Field(
        default=None,
        description="Optional text chunk from LLM generation.",
    )
    audio_chunk: bytes | None = Field(
        default=None,
        description="Optional audio chunk bytes (binary WAV data).",
    )
    blendshapes: dict[str, float] | None = Field(
        default=None,
        description="Optional blendshape weights (viseme_name -> weight 0.0-1.0).",
    )
    motion: dict[str, tuple[float, float, float, float]] | None = Field(
        default=None,
        description="Optional bone rotations as quaternions (bone_name -> (x, y, z, w)).",
    )


class ChatResponse(BaseModel):
    """Ответ для POST /api/v1/chat (non-streaming).

    Содержит полный результат обработки запроса: текст, аудио, анимации.
    Аудио кодируется в base64 для передачи через JSON.

    Attributes:
        full_text: Полный сгенерированный текст ответа от LLM.
        audio: Аудио-сегмент TTS (с base64-кодированными байтами).
        blendshapes: Blendshape-анимация для синхронизации губ с аудио.
        motion: Motion-анимация скелета (жест/эмоция на основе sentiment analysis).
        processing_time: Общее время обработки запроса в секундах.
    """

    full_text: str = Field(
        ...,
        description="Full generated text response from LLM.",
    )
    audio: AudioSegmentResponse = Field(
        ...,
        description="TTS audio segment with base64-encoded data.",
    )
    blendshapes: BlendshapeWeights = Field(
        ...,
        description="Lipsync blendshape animation frames.",
    )
    motion: MotionKeyframes = Field(
        ...,
        description="Motion animation keyframes for skeleton.",
    )
    processing_time: float = Field(
        ...,
        ge=0.0,
        description="Total processing time in seconds.",
    )
