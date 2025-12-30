"""Интерфейс Text-to-Speech Engine.

Абстракция для синтеза речи (XTTS-v2, Silero), как задано в SPEC.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from avatar.schemas.audio_types import AudioSegment


class ITTSEngine(ABC):
    """Интерфейс TTS-движка."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "ru",
        speaker_wav: str | None = None,
    ) -> AudioSegment:
        """Синтез речи из текста (non-streaming).

        Args:
            text: Текст для озвучки.
            language: Язык синтеза (по умолчанию русский).
            speaker_wav: Опциональный путь к WAV для voice cloning.

        Returns:
            AudioSegment: Аудио-сегмент с метаданными.

        Raises:
            ValueError: Если текст пустой или язык не поддерживается.
            RuntimeError: Если синтез завершился ошибкой.
        """
        raise NotImplementedError("TODO: Implement synthesize")

    @abstractmethod
    async def synthesize_streaming(
        self,
        text: str,
        language: str = "ru",
    ) -> AsyncIterator[AudioSegment]:
        """Синтез речи (streaming).

        Args:
            text: Текст для озвучки.
            language: Язык синтеза.

        Yields:
            AudioSegment: Аудио-чанки по мере генерации.

        Raises:
            ValueError: Если текст пустой или язык не поддерживается.
            RuntimeError: Если синтез завершился ошибкой.
        """
        raise NotImplementedError("TODO: Implement synthesize_streaming")
        yield  # type: ignore[unreachable]

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """Список поддерживаемых языков.

        Returns:
            list[str]: Коды языков (например, ["ru", "en"]).
        """
        raise NotImplementedError("TODO: Implement get_supported_languages")
