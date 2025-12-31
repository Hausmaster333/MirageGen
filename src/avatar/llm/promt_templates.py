"""Шаблоны системных промптов для русского языка.

Используются для настройки поведения LLM.
"""

from __future__ import annotations

RUSSIAN_SYSTEM_PROMPT = """Ты — дружелюбный русскоязычный AI-ассистент.
ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ
Отвечай кратко, естественно и по-русски.
Используй эмоциональные выражения, когда это уместно."""

CONVERSATION_SYSTEM_PROMPT = """Ты — виртуальный аватар, который общается с пользователем через текст и анимацию.
ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.
Отвечай кратко (1-3 предложения), эмоционально и на русском языке.
Если пользователь задаёт вопрос, ответь по существу.
Если пользователь выражает эмоцию, поддержи её соответствующей реакцией."""

# ENGLISH_SYSTEM_PROMPT = """You are a friendly AI assistant.
# Answer concisely and naturally.
# Use emotional expressions when appropriate."""


def get_system_prompt(language: str = "ru") -> str:
    """Получить системный промпт для языка.

    Args:
        language: Код языка ("ru" или "en").

    Returns:
        str: Системный промпт.

    Raises:
        ValueError: Если язык не поддерживается.
    """
    prompts = {
        "ru": CONVERSATION_SYSTEM_PROMPT,
        # "en": ENGLISH_SYSTEM_PROMPT,
    }

    if language not in prompts:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(prompts.keys())}")

    return prompts[language]
