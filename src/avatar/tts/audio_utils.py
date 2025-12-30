"""Утилиты для обработки аудио (конвертация, нормализация).

Используется для работы с WAV/MP3, librosa, pydub.
"""

from __future__ import annotations

import io
from pathlib import Path

from loguru import logger
from pydub import AudioSegment as PydubSegment

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
    try:
        # Создаем директорию, если нет
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Определяем формат по расширению файла или из метаданных
        file_format = output_path.suffix.lstrip(".").lower()
        if not file_format:
            file_format = audio.format

        valid_formats = ["wav", "mp3"]
        if file_format not in valid_formats:
            raise ValueError(f"Unsupported format: {file_format}. Use: {valid_formats}")

        with Path(output_path).open("wb") as f:
            f.write(audio.audio_bytes)

        logger.debug(f"Audio saved to {output_path}")

    except Exception as e:
        logger.error(f"Failed to save audio to {output_path}: {e}")
        raise OSError(f"Failed to save audio: {e}") from e


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
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    try:
        # Загружаем через Pydub для получения метаданных
        audio_data = PydubSegment.from_file(str(audio_path))

        # Получаем сырые данные
        buffer = io.BytesIO()
        audio_format = "wav"  # Конвертируем все в wav для унификации
        audio_data.export(buffer, format=audio_format)
        audio_bytes = buffer.getvalue()

        return AudioSegment(
            audio_bytes=audio_bytes,
            sample_rate=audio_data.frame_rate,
            format=audio_format,
            duration=audio_data.duration_seconds,
        )
    except Exception as e:
        logger.error(f"Failed to load audio from {audio_path}: {e}")
        raise ValueError(f"Failed to load audio: {e}") from e


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
    try:
        segment = PydubSegment.from_wav(io.BytesIO(audio_bytes))

        change_in_db = target_db - segment.dBFS
        normalized_segment = segment.apply_gain(change_in_db)

        buffer = io.BytesIO()
        normalized_segment.export(buffer, format="wav")
        return buffer.getvalue()

    except Exception as e:
        logger.warning(f"Audio normalization failed, returning original: {e}")
        return audio_bytes


def convert_sample_rate(audio_bytes: bytes, from_sr: int, to_sr: int) -> bytes:
    """Конвертировать частоту дискретизации.

    Args:
        audio_bytes: Байты аудио (WAV).
        from_sr: Исходная частота (для справки, Pydub сам определит из заголовка WAV).
        to_sr: Целевая частота.

    Returns:
        bytes: Конвертированные байты аудио.

    Raises:
        ValueError: Если частоты некорректны.
    """
    if from_sr == to_sr:
        return audio_bytes

    try:
        segment = PydubSegment.from_wav(io.BytesIO(audio_bytes))

        # Ресемплинг
        resampled_segment = segment.set_frame_rate(to_sr)

        buffer = io.BytesIO()
        resampled_segment.export(buffer, format="wav")
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"Sample rate conversion failed: {e}")
        raise ValueError(f"Conversion failed: {e}") from e
