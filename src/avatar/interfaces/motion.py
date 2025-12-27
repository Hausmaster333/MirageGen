"""Интерфейс Motion/Gesture Generator.

Абстракция для генерации скелетной анимации на основе эмоции/жеста, как задано в SPEC.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from avatar.schemas.animation_types import MotionKeyframes


class IMotionGenerator(ABC):
    """Интерфейс генератора motion-анимации."""

    @abstractmethod
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
            RuntimeError: Если генерация/загрузка preset не удалась.
        """
        raise NotImplementedError("TODO: Implement generate_motion")

    @abstractmethod
    def get_available_actions(self) -> list[str]:
        """Список доступных действий/preset.

        Returns:
            list[str]: Например, ["idle", "happy_gesture", "thinking_gesture"].
        """
        raise NotImplementedError("TODO: Implement get_available_actions")
