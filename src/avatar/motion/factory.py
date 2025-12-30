# === Файл: src/avatar/motion/factory.py ===
"""Factory для создания Motion генераторов."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from avatar.motion.preset_loader import PresetMotionGenerator

if TYPE_CHECKING:
    from avatar.config.settings import MotionConfig
    from avatar.interfaces.motion import IMotionGenerator


class MotionFactory:
    """Factory для создания Motion генераторов."""

    @staticmethod
    def create(config: MotionConfig) -> IMotionGenerator:
        """Создать Motion генератор на основе конфигурации.

        Args:
            config: Конфигурация Motion.

        Returns:
            IMotionGenerator: Инстанс генератора.

        Raises:
            ValueError: Если генератор не поддерживается.
        """
        generator = config.generator.lower()

        if generator == "preset":
            logger.info(f"Creating PresetMotionGenerator with dir={config.animations_dir}")
            return PresetMotionGenerator(
                animations_dir=config.animations_dir,
                fallback_action=config.fallback_action,
            )

        # Будущие генераторы:
        # if generator == "t2m-gpt":
        #     return T2MGenerator()

        raise ValueError(f"Unsupported Motion generator: {generator}. Supported: preset")
