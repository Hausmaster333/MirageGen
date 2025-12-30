# === Файл: src/avatar/llm/factory.py ===
"""Factory для создания LLM провайдеров на основе конфига."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from avatar.llm.ollama_provider import OllamaProvider

if TYPE_CHECKING:
    from avatar.config.settings import LLMConfig
    from avatar.interfaces.llm import ILLMProvider


class LLMFactory:
    """Factory для создания LLM провайдеров."""

    @staticmethod
    def create(config: LLMConfig) -> ILLMProvider:
        """Создать LLM провайдера на основе конфигурации.

        Args:
            config: Конфигурация LLM.

        Returns:
            ILLMProvider: Инстанс провайдера.

        Raises:
            ValueError: Если провайдер не поддерживается.
        """
        provider = config.provider.lower()

        if provider == "ollama":
            logger.info(f"Creating OllamaProvider with model={config.model}")
            return OllamaProvider(
                model=config.model,
                base_url=config.base_url,
                system_prompt=config.system_prompt_ru,
            )

        # Будущие провайдеры:
        # if provider == "openai":
        #     return OpenAIProvider(api_key=config.api_key, model=config.model)
        #
        # if provider == "anthropic":
        #     return AnthropicProvider(api_key=config.api_key, model=config.model)

        raise ValueError(
            f"Unsupported LLM provider: {provider}. Supported: ollama, openai (future), anthropic (future)"
        )
