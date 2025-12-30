# === Файл: src/avatar/pipeline/streaming_manager.py ===
"""Streaming Manager (Observer Pattern для WebSocket broadcasts).

Управляет подписчиками и broadcast фреймов через WebSocket.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from avatar.schemas.api_types import AvatarFrame


class StreamingManager:
    """Streaming Manager (Observer Pattern).

    Attributes:
        _observers: Список подписчиков (callback-функций для broadcast).
    """

    def __init__(self) -> None:
        """Инициализация StreamingManager."""
        self._observers: list[Callable[[Any], Any]] = []
        logger.info("StreamingManager initialized")

    def subscribe(self, observer: Callable[[Any], Any]) -> None:
        """Подписать observer на broadcast событий.

        Args:
            observer: Callback-функция для обработки AvatarFrame.
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer subscribed: {observer}")

    def unsubscribe(self, observer: Callable[[Any], Any]) -> None:
        """Отписать observer от broadcast событий.

        Args:
            observer: Callback-функция для удаления.
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"Observer unsubscribed: {observer}")

    async def broadcast(self, frame: AvatarFrame) -> None:
        """Broadcast фрейма всем подписчикам.

        Поддерживает sync и async callbacks. Ошибки отдельных подписчиков не валят broadcast.

        Args:
            frame: AvatarFrame для отправки.
        """
        if not self._observers:
            return

        for observer in list(self._observers):
            try:
                result = observer(frame)
                # Если callback async
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.exception(f"Observer broadcast failed for {observer}: {e}")
                # Удаляем сломанных подписчиков (например, закрытые websocket)
                try:
                    self.unsubscribe(observer)
                except Exception:
                    logger.warning("Failed to unsubscribe broken observer", exc_info=True)

    async def broadcast_error(self, error_message: str) -> None:
        """Broadcast сообщения об ошибке всем подписчикам.

        Args:
            error_message: Текст ошибки.
        """
        if not self._observers:
            return

        # Формат для WebSocket API
        error_payload = {"type": "error", "message": error_message}

        for observer in list(self._observers):
            try:
                result = observer(error_payload)
                if hasattr(result, "__await__"):
                    await result
            except Exception as e:
                logger.exception(f"Observer error broadcast failed for {observer}: {e}")
                try:
                    self.unsubscribe(observer)
                except Exception:
                    logger.warning("Failed to unsubscribe broken observer", exc_info=True)

    def get_observer_count(self) -> int:
        """Получить количество активных подписчиков.

        Returns:
            int: Количество подписчиков.
        """
        return len(self._observers)
