"""Интерфейс Language Model Provider (LLM).

Абстракция для генерации текста (синхронная + стриминговая), как задано в SPEC.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from avatar.schemas.llm_types import LLMResponse, Message


class ILLMProvider(ABC):
    """Интерфейс провайдера LLM (Ollama, OpenAI, Anthropic, etc.)."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Генерация текста (non-streaming).

        Args:
            messages: История диалога (список Message).
            temperature: Температура генерации.
            max_tokens: Максимальное количество токенов.

        Returns:
            LLMResponse: Результат генерации с текстом и метаданными.

        Raises:
            RuntimeError: Если модель недоступна или генерация не удалась.
        """
        raise NotImplementedError("TODO: Implement generate")

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Генерация текста (streaming).

        Args:
            messages: История диалога (список Message).
            temperature: Температура генерации.
            max_tokens: Максимальное количество токенов.

        Yields:
            str: Токены/чанки текста по мере генерации.

        Raises:
            RuntimeError: Если модель недоступна или генерация не удалась.
        """
        raise NotImplementedError("TODO: Implement generate_stream")
        yield  # type: ignore[unreachable]

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Проверка доступности LLM.

        Returns:
            bool: True, если LLM-сервис отвечает.

        Raises:
            ConnectionError: Если сервис недоступен.
        """
        raise NotImplementedError("TODO: Implement healthcheck")
