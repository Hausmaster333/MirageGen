# === Файл: src/avatar/lipsync/factory.py ===
"""Factory для создания Lipsync генераторов."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from avatar.lipsync.rhubarb_generator import RhubarbGenerator

if TYPE_CHECKING:
    from avatar.config.settings import LipSyncConfig
    from avatar.interfaces.lipsync import ILipSyncGenerator


class LipSyncFactory:
    """Factory для создания Lipsync генераторов."""

    @staticmethod
    def create(config: LipSyncConfig) -> ILipSyncGenerator:
        """Создать Lipsync генератор на основе конфигурации.

        Args:
            config: Конфигурация Lipsync.

        Returns:
            ILipSyncGenerator: Инстанс генератора.

        Raises:
            ValueError: Если генератор не поддерживается.
        """
        generator = config.generator.lower()

        if generator == "rhubarb":
            logger.info(f"Creating RhubarbGenerator at {config.rhubarb_path}")
            return RhubarbGenerator(
                rhubarb_path=config.rhubarb_path,
                recognizer=config.recognizer,
            )

        # Будущие генераторы:
        # if generator == "wav2lip":
        #     return Wav2LipGenerator()

        raise ValueError(f"Unsupported Lipsync generator: {generator}. Supported: rhubarb")
