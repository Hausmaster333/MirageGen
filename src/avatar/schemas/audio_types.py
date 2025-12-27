# === Файл: src/avatar/schemas/audiotypes.py ===
"""Pydantic-модели аудио-данных.

Используется TTS-движком и API (bytes + sample rate + формат + длительность),
как это задано в SPEC.md.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AudioSegment(BaseModel):
    """Аудио-сегмент, возвращаемый TTS.

    Attributes:
        audio_bytes: Байты аудио (обычно WAV/MP3).
        sample_rate: Частота дискретизации (по умолчанию 24000).
        format: Формат контейнера ("wav" или "mp3").
        duration: Длительность аудио в секундах.
    """

    audio_bytes: bytes = Field(..., description="Raw audio bytes.")
    sample_rate: int = Field(default=24000, ge=1, description="Sample rate (Hz).")
    format: Literal["wav", "mp3"] = Field(default="wav", description="Audio container format.")
    duration: float = Field(..., ge=0.0, description="Duration in seconds.")
