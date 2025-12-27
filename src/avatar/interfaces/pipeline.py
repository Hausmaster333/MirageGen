"""Интерфейс Pipeline Orchestrator.

Главный оркестратор: LLM → TTS → Lipsync → Motion → WebSocket, как задано в SPEC.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from avatar.schemas.api_types import AvatarFrame
    from avatar.schemas.llm_types import Message


class IPipeline(ABC):
    """Интерфейс оркестратора пайплайна."""

    @abstractmethod
    async def process(
        self,
        user_input: str,
        conversation_history: list[Message] | None = None,
    ) -> AsyncIterator[AvatarFrame]:
        """Обработка текста пользователя → стриминг AvatarFrame.

        Args:
            user_input: Текст запроса пользователя.
            conversation_history: Опциональная история диалога.

        Yields:
            AvatarFrame: Кадры с текстом/аудио/blendshapes/motion.

        Raises:
            ValueError: Если user_input пустой или слишком длинный.
            RuntimeError: Если любой из компонентов пайплайна упал.
        """
        raise NotImplementedError("TODO: Implement process")
        yield  # type: ignore[unreachable]

    @abstractmethod
    async def healthcheck(self) -> dict[str, bool]:
        """Healthcheck всех компонентов пайплайна.

        Returns:
            dict[str, bool]: Статус компонентов (llm/tts/lipsync/motion).
        """
        raise NotImplementedError("TODO: Implement healthcheck")
