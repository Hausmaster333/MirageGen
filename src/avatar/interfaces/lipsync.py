"""Интерфейс Lip-Sync Generator.

Абстракция для генерации blendshape-анимации из аудио (Rhubarb), как задано в SPEC.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from avatar.schemas.animation_types import BlendshapeWeights


class ILipSyncGenerator(ABC):
    """Интерфейс генератора lip-sync анимации."""

    @abstractmethod
    async def generate_blendshapes(
        self,
        audio_path: Path,
        recognizer: str = "pocketSphinx",
    ) -> BlendshapeWeights:
        """Генерация blendshape-кадров из аудио.

        Args:
            audio_path: Путь к аудио-файлу (WAV).
            recognizer: Phonetic recognizer ("pocketSphinx" или "phonetic").

        Returns:
            BlendshapeWeights: Набор кадров blendshape с таймстампами.

        Raises:
            FileNotFoundError: Если audio_path не существует.
            RuntimeError: Если Rhubarb/бинарь завершился ошибкой.
        """
        raise NotImplementedError("TODO: Implement generate_blendshapes")

    @abstractmethod
    def get_phoneme_mapping(self) -> dict[str, str]:
        """Mapping Rhubarb-фонем → Three.js blendshape-имён.

        Returns:
            dict[str, str]: Например, {"A": "viseme_aa", "B": "viseme_PP", ...}.
        """
        raise NotImplementedError("TODO: Implement get_phoneme_mapping")
