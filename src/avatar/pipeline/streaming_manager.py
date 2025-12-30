# === Файл: src/avatar/pipeline/streaming_manager.py ===
"""Streaming Manager (Observer Pattern для WebSocket broadcasts).

Управляет подписчиками и broadcast фреймов через WebSocket.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from avatar.schemas.api_types import AvatarFrame


class StreamingManager:
    """Streaming Manager (Observer Pattern).

    Attributes:
        observers: Список подписчиков (callback-функций для broadcast).
    """

    def __init__(self) -> None:
        """Инициализация StreamingManager."""
        self._observers: list[Callable[[AvatarFrame], None]] = []
        logger.info("StreamingManager initialized")

    def subscribe(self, observer: Callable[[AvatarFrame], None]) -> None:
        """Подписать observer на broadcast событий.

        Args:
            observer: Callback-функция для обработки AvatarFrame.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer subscribed: {observer}")

    def unsubscribe(self, observer: Callable[[AvatarFrame], None]) -> None:
        """Отписать observer от broadcast событий.

        Args:
            observer: Callback-функция для удаления.
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer unsubscribed: {observer}")

    async def broadcast(self, frame: AvatarFrame) -> None:
        """Broadcast фрейма всем подписчикам.

        Args:
            frame: AvatarFrame для отправки.
        """
        raise NotImplementedError("TODO: Implement broadcast")

    async def broadcast_error(self, error_message: str) -> None:
        """Broadcast сообщения об ошибке всем подписчикам.

        Args:
            error_message: Текст ошибки.
        """
        raise NotImplementedError("TODO: Implement broadcast_error")

    def get_observer_count(self) -> int:
        """Получить количество активных подписчиков.

        Returns:
            int: Количество подписчиков.
        """
        return len(self._observers)
