"""Тесты для OllamaProvider (с mock)."""

import pytest
from avatar.schemas.llm_types import Message


@pytest.mark.asyncio
async def test_llm_generate(mock_llm):
    """Тест генерации LLM."""
    messages = [Message(role="user", content="Привет!")]
    response = await mock_llm.generate(messages)
    
    assert response.text == "Mock LLM response"
    assert response.tokens_count > 0
    assert response.generation_time >= 0.0


@pytest.mark.asyncio
async def test_llm_stream(mock_llm):
    """Тест стриминговой генерации LLM."""
    messages = [Message(role="user", content="Привет!")]
    chunks = []
    
    async for chunk in mock_llm.generate_stream(messages):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert "Mock" in "".join(chunks)


@pytest.mark.asyncio
async def test_llm_healthcheck(mock_llm):
    """Тест healthcheck LLM."""
    is_healthy = await mock_llm.healthcheck()
    assert is_healthy is True
