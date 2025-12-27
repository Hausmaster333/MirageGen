# === Файл: src/avatar/motion/preset_loader.py ===
"""Preset Motion Loader (загрузка preset-анимаций из JSON).

Используется для быстрой генерации motion на основе emotion-лейблов.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from avatar.interfaces.motion import IMotionGenerator
from avatar.schemas.animation_types import MotionKeyframe, MotionKeyframes

if TYPE_CHECKING:
    pass


class PresetMotionGenerator(IMotionGenerator):
    """Preset Motion Generator (загрузка JSON-анимаций).

    Attributes:
        animations_dir: Директория с preset-анимациями (idle.json, happy_gesture.json, ...).
        fallback_action: Дефолтное действие при ошибке.
        presets: Кэш загруженных preset-анимаций.
    """

    def __init__(
        self,
        animations_dir: Path = Path("assets/animations"),
        fallback_action: str = "idle",
    ) -> None:
        """Инициализация PresetMotionGenerator.

        Args:
            animations_dir: Директория с preset JSON.
            fallback_action: Дефолтное действие при ошибке.

        Raises:
            FileNotFoundError: Если animations_dir не существует.
        """
        if not animations_dir.exists():
            msg = f"Animations directory not found: {animations_dir}"
            raise FileNotFoundError(msg)
        self.animations_dir = animations_dir
        self.fallback_action = fallback_action
        self._presets: dict[str, MotionKeyframes] = {}
        logger.info(f"PresetMotionGenerator initialized: animations_dir={animations_dir}")

    async def generate_motion(
        self,
        emotion: str,
        duration: float,
        action_hint: str | None = None,
    ) -> MotionKeyframes:
        """Генерация motion-keyframes на основе эмоции.

        Args:
            emotion: Эмоция ("happy", "sad", "neutral", "thinking").
            duration: Длительность анимации в секундах.
            action_hint: Опциональная подсказка действия (например, "gesture").

        Returns:
            MotionKeyframes: Keyframes скелетной анимации.

        Raises:
            ValueError: Если эмоция не поддерживается.
            RuntimeError: Если загрузка preset не удалась.
        """
        raise NotImplementedError("TODO: Implement generate_motion")

    def get_available_actions(self) -> list[str]:
        """Список доступных действий/preset.

        Returns:
            list[str]: Имена preset (например, ["idle", "happy_gesture", "thinking_gesture"]).
        """
        raise NotImplementedError("TODO: Implement get_available_actions")

    def _load_preset(self, preset_name: str) -> MotionKeyframes:
        """Загрузить preset-анимацию из JSON.

        Args:
            preset_name: Имя preset (например, "idle").

        Returns:
            MotionKeyframes: Загруженные keyframes.

        Raises:
            FileNotFoundError: Если файл preset не найден.
            ValueError: Если JSON невалиден.
        """
        raise NotImplementedError("TODO: Implement _load_preset")

    def _map_emotion_to_preset(self, emotion: str, action_hint: str | None) -> str:
        """Маппинг эмоции → имя preset.

        Args:
            emotion: Эмоция.
            action_hint: Опциональная подсказка действия.

        Returns:
            str: Имя preset (например, "happy_gesture").
        """
        emotion_map = {
            "happy": "happy_gesture",
            "sad": "sad_gesture",
            "neutral": "idle",
            "thinking": "thinking_gesture",
        }
        return emotion_map.get(emotion, self.fallback_action)
