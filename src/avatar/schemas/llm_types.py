# === Файл: src/avatar/schemas/llmtypes.py ===
"""Pydantic-модели для сообщений и ответа LLM.

Модели описывают формат истории диалога и результат генерации (включая action),
как это задано в SPEC.md.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Сообщение в истории диалога для LLM.

    Attributes:
        role: Роль отправителя (user/assistant/system).
        content: Текст сообщения.
    """

    role: Literal["user", "assistant", "system"] = Field(..., description="Sender role.")
    content: str = Field(..., description="Message text content.")


class LLMResponse(BaseModel):
    """Результат генерации LLM (нестриминговый).

    Attributes:
        text: Сгенерированный текст.
        action: Опциональная подсказка действия (например, жест/анимация).
        tokens_count: Количество сгенерированных токенов.
        generation_time: Время генерации в секундах.
    """

    text: str = Field(..., description="Generated text.")
    action: str | None = Field(default=None, description="Optional action hint.")
    tokens_count: int = Field(..., ge=0, description="Generated tokens count.")
    generation_time: float = Field(..., ge=0.0, description="Generation time (seconds).")
