"""Ollama LLM Provider implementation (Mistral 7B, Qwen).

Использует библиотеку `ollama` для взаимодействия с локальным Ollama-сервером.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, AsyncIterator

from loguru import logger
from ollama import AsyncClient

from avatar.interfaces.llm import ILLMProvider
from avatar.schemas.llm_types import LLMResponse, Message

if TYPE_CHECKING:
    pass


class OllamaProvider(ILLMProvider):
    """Ollama LLM Provider (Mistral 7B, Qwen и другие модели).

    Attributes:
        model: Название модели (например, "mistral:7b-instruct-q4_K_M").
        base_url: URL Ollama-сервера.
        system_prompt: Системный промпт для русского языка.
        client: Async-клиент Ollama.
    """

    def __init__(
        self,
        model: str = "mistral:7b-instruct-q4_K_M",
        base_url: str = "http://localhost:11434",
        system_prompt: str = "Ты — дружелюбный русскоязычный AI-ассистент.",
    ) -> None:
        """Инициализация Ollama Provider.

        Args:
            model: Название модели Ollama.
            base_url: URL Ollama-сервера.
            system_prompt: Системный промпт.
        """
        self.model = model
        self.base_url = base_url
        self.system_prompt = system_prompt
        self.client = AsyncClient(host=base_url)
        logger.info(f"OllamaProvider initialized: model={model}, base_url={base_url}")

    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Генерация текста (non-streaming).

        Args:
            messages: История диалога.
            temperature: Температура генерации.
            max_tokens: Максимальное количество токенов.

        Returns:
            LLMResponse: Результат генерации.

        Raises:
            RuntimeError: Если Ollama-сервер недоступен или ошибка генерации.
        """
        raise NotImplementedError("TODO: Implement generate")

    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Генерация текста (streaming).

        Args:
            messages: История диалога.
            temperature: Температура генерации.
            max_tokens: Максимальное количество токенов.

        Yields:
            str: Токены текста.

        Raises:
            RuntimeError: Если Ollama-сервер недоступен или ошибка генерации.
        """
        raise NotImplementedError("TODO: Implement generate_stream")
        yield  # type: ignore[unreachable]

    async def healthcheck(self) -> bool:
        """Проверка доступности Ollama-сервера.

        Returns:
            bool: True, если сервер отвечает.

        Raises:
            ConnectionError: Если сервер недоступен.
        """
        raise NotImplementedError("TODO: Implement healthcheck")
