"""Ollama LLM Provider implementation (Mistral 7B, Qwen).

Использует библиотеку `ollama` для взаимодействия с локальным Ollama-сервером.
"""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, AsyncIterator

from loguru import logger
from ollama import AsyncClient, ResponseError

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
        system_prompt: str = "Ты дружелюбный русскоязычный AI-ассистент. Ты ВСЕГДА отвечаешь ТОЛЬКО на русском языке, даже если вопрос задан на английском.",  
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
            temperature: Температура генерации (0.0-2.0).
            max_tokens: Максимальное количество токенов (1-4096).

        Returns:
            LLMResponse: Результат генерации.

        Raises:
            ValueError: Если messages пустой или параметры некорректны.
            RuntimeError: Если Ollama-сервер недоступен или ошибка генерации.
        """
        # Валидация входных данных
        if not messages:
            raise ValueError("messages list cannot be empty")

        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")

        if not 1 <= max_tokens <= 4096:
            raise ValueError(f"max_tokens must be between 1 and 4096, got {max_tokens}")

        # Подготовка сообщений для Ollama API
        formatted_messages = self._format_messages(messages)

        logger.debug(
            f"Generating response: model={self.model}, "
            f"temperature={temperature}, max_tokens={max_tokens}, "
            f"messages_count={len(messages)}"
        )

        start_time = time.time()

        try:
            # Вызов Ollama API (non-streaming)
            response = await self.client.chat(
                model=self.model,
                messages=formatted_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=False,
            )

            generation_time = time.time() - start_time

            # Извлечение текста и метаданных
            text = response.get("message", {}).get("content", "")
            tokens_count = response.get("eval_count", 0)

            # Попытка извлечь action hint из ответа (опционально)
            action = self._extract_action_hint(text)

            logger.info(
                f"Generated response: {len(text)} chars, "
                f"{tokens_count} tokens, {generation_time:.2f}s"
            )

            return LLMResponse(
                text=text,
                action=action,
                tokens_count=tokens_count,
                generation_time=generation_time,
            )

        except ResponseError as e:
            logger.error(f"Ollama API error: {e}")
            raise RuntimeError(f"Failed to generate response from Ollama: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            raise RuntimeError(f"Unexpected error during LLM generation: {e}") from e

    async def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
    ) -> AsyncIterator[str]:
        """Генерация текста (streaming).

        Args:
            messages: История диалога.
            temperature: Температура генерации (0.0-2.0).
            max_tokens: Максимальное количество токенов (1-4096).

        Yields:
            str: Токены текста по мере генерации.

        Raises:
            ValueError: Если messages пустой или параметры некорректны.
            RuntimeError: Если Ollama-сервер недоступен или ошибка генерации.
        """
        # Валидация входных данных
        if not messages:
            raise ValueError("messages list cannot be empty")

        if not 0.0 <= temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {temperature}")

        if not 1 <= max_tokens <= 4096:
            raise ValueError(f"max_tokens must be between 1 and 4096, got {max_tokens}")

        # Подготовка сообщений
        formatted_messages = self._format_messages(messages)

        logger.debug(
            f"Starting streaming generation: model={self.model}, "
            f"temperature={temperature}, max_tokens={max_tokens}"
        )

        token_count = 0
        start_time = time.time()

        try:
            # Вызов Ollama API (streaming)
            stream = await self.client.chat(
                model=self.model,
                messages=formatted_messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                stream=True,
            )

            # Итерация по stream chunks
            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    token = chunk["message"]["content"]
                    if token:  # Пропускаем пустые токены
                        token_count += 1
                        yield token

            generation_time = time.time() - start_time
            logger.info(
                f"Streaming completed: {token_count} tokens generated in {generation_time:.2f}s"
            )

        except ResponseError as e:
            logger.error(f"Ollama streaming error: {e}")
            raise RuntimeError(f"Failed to stream response from Ollama: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            raise RuntimeError(f"Unexpected streaming error: {e}") from e

    async def healthcheck(self) -> bool:
        """Проверка доступности Ollama-сервера.

        Returns:
            bool: True, если сервер отвечает и модель доступна.

        Raises:
            ConnectionError: Если сервер недоступен.
        """
        logger.debug(f"Healthcheck: {self.base_url}, model={self.model}")

        try:
            # Проверка доступности сервера и списка моделей
            response = await self.client.list()

            # Извлечение списка моделей (защита от разных форматов ответа)
            models = response.get("models", [])
            
            if not models:
                logger.warning("No models available in Ollama")
                return False

            # Получить имена моделей (поддержка dict и объектов)
            available_models = []
            for model in models:
                # Если model - это dict
                if isinstance(model, dict):
                    model_name = model.get("name") or model.get("model")
                # Если model - это объект с атрибутами
                elif hasattr(model, "name"):
                    model_name = model.name
                elif hasattr(model, "model"):
                    model_name = model.model
                else:
                    model_name = str(model)
                
                if model_name:
                    available_models.append(model_name)

            logger.debug(f"Available models: {available_models}")

            if self.model not in available_models:
                logger.warning(
                    f"Model {self.model} not found in available models: {available_models}"
                )
                return False

            logger.info(f"Healthcheck passed: model {self.model} is available")
            return True

        except ResponseError as e:
            logger.error(f"Ollama healthcheck failed (ResponseError): {e}")
            raise ConnectionError(f"Ollama server error: {e}") from e
        except Exception as e:
            logger.error(f"Ollama healthcheck failed: {e}")
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}: {e}"
            ) from e


    def _format_messages(self, messages: list[Message]) -> list[dict[str, str]]:
        """Преобразовать Message в формат Ollama API.

        Args:
            messages: Список сообщений.

        Returns:
            list[dict]: Сообщения в формате Ollama.
        """
        formatted = []

        # Добавить системный промпт, если он не в начале
        if not messages or messages[0].role != "system":
            formatted.append({
                "role": "system",
                "content": self.system_prompt,
            })

        # Добавить все сообщения
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content,
            })

        return formatted

    def _extract_action_hint(self, text: str) -> str | None:
        """Извлечь action hint из текста LLM (если присутствует).

        Некоторые модели могут возвращать специальные теги вроде [ACTION:happy].

        Args:
            text: Текст ответа LLM.

        Returns:
            str | None: Название действия или None.
        """
        # Поиск паттерна [ACTION:название]
        match = re.search(r"\[ACTION:(\w+)\]", text)
        if match:
            action = match.group(1).lower()
            logger.debug(f"Extracted action hint: {action}")
            return action

        return None
