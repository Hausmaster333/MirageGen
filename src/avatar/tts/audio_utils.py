"""Утилиты для обработки аудио (конвертация, нормализация).

Используется для работы с WAV/MP3, librosa, pydub.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from avatar.schemas.audio_types import AudioSegment


def save_audio_segment(audio: AudioSegment, output_path: Path) -> None:
    """Сохранить AudioSegment в файл.

    Args:
        audio: Аудио-сегмент.
        output_path: Путь для сохранения (WAV или MP3).

    Raises:
        ValueError: Если формат не поддерживается.
        IOError: Если запись в файл не удалась.
    """
    raise NotImplementedError("TODO: Implement save_audio_segment")


def load_audio_segment(audio_path: Path) -> AudioSegment:
    """Загрузить аудио из файла в AudioSegment.

    Args:
        audio_path: Путь к аудио-файлу.

    Returns:
        AudioSegment: Аудио-сегмент.

    Raises:
        FileNotFoundError: Если файл не существует.
        ValueError: Если формат не поддерживается.
    """
    raise NotImplementedError("TODO: Implement load_audio_segment")


def normalize_audio(audio_bytes: bytes, target_db: float = -20.0) -> bytes:
    """Нормализовать громкость аудио.

    Args:
        audio_bytes: Байты аудио (WAV).
        target_db: Целевая громкость в дБ.

    Returns:
        bytes: Нормализованные байты аудио.

    Raises:
        ValueError: Если аудио не валидно.
    """
    raise NotImplementedError("TODO: Implement normalize_audio")


def convert_sample_rate(audio_bytes: bytes, from_sr: int, to_sr: int) -> bytes:
    """Конвертировать частоту дискретизации.

    Args:
        audio_bytes: Байты аудио (WAV).
        from_sr: Исходная частота.
        to_sr: Целевая частота.

    Returns:
        bytes: Конвертированные байты аудио.

    Raises:
        ValueError: Если частоты некорректны.
    """
    raise NotImplementedError("TODO: Implement convert_sample_rate")
