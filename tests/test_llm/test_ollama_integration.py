"""Интеграционные тесты для OllamaProvider с реальным Mistral."""

import pytest
from ollama import ResponseError

from avatar.llm.ollama_provider import OllamaProvider
from avatar.schemas.llm_types import Message


# Проверка доступности Ollama перед запуском тестов
@pytest.fixture(scope="function")
async def ollama_provider():
    """Fixture для реального OllamaProvider."""
    provider = OllamaProvider(
        model="mistral:7b-instruct-q4_K_M",
        base_url="http://localhost:11434",
    )
    
    # Проверить, что Ollama доступен
    try:
        is_healthy = await provider.healthcheck()
        if not is_healthy:
            pytest.skip("Ollama server is not available or model not found")
    except Exception:
        pytest.skip("Cannot connect to Ollama server")
    
    return provider


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_healthcheck(ollama_provider):
    """Тест: проверка доступности Ollama и модели Mistral."""
    is_healthy = await ollama_provider.healthcheck()
    
    assert is_healthy is True, "Ollama healthcheck failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_generate_simple(ollama_provider):
    """Тест: простая генерация текста."""
    messages = [
        Message(role="user", content="Привет! Как дела?")
    ]
    
    response = await ollama_provider.generate(messages, temperature=0.7, max_tokens=100)
    
    # Проверки
    assert response.text is not None
    assert len(response.text) > 0, "Generated text is empty"
    assert response.tokens_count > 0, "Token count should be positive"
    assert response.generation_time >= 0.0, "Generation time should be non-negative"
    
    print(f"\n✅ Generated: {response.text}")
    print(f"⏱️  Time: {response.generation_time:.2f}s")
    print(f"🔢 Tokens: {response.tokens_count}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_generate_with_history(ollama_provider):
    """Тест: генерация с историей диалога."""
    messages = [
        Message(role="user", content="Меня зовут Алекс."),
        Message(role="assistant", content="Приятно познакомиться, Алекс!"),
        Message(role="user", content="Как меня зовут?"),
    ]
    
    response = await ollama_provider.generate(messages, temperature=0.5, max_tokens=50)
    
    assert response.text is not None
    assert len(response.text) > 0
    # Проверить, что модель помнит имя
    assert "алекс" in response.text.lower(), "Model should remember the name from context"
    
    print(f"\n✅ Context-aware response: {response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_generate_stream(ollama_provider):
    """Тест: потоковая генерация текста."""
    messages = [
        Message(role="user", content="Расскажи короткую историю про кота.")
    ]
    
    chunks = []
    token_count = 0
    
    async for chunk in ollama_provider.generate_stream(messages, temperature=0.8, max_tokens=150):
        chunks.append(chunk)
        token_count += 1
        print(chunk, end="", flush=True)  # Печатать токены в реальном времени
    
    full_text = "".join(chunks)
    
    assert len(chunks) > 0, "No chunks received from stream"
    assert len(full_text) > 0, "Generated text is empty"
    assert token_count > 0, "Token count should be positive"
    
    print(f"\n\n✅ Streamed {token_count} tokens")
    print(f"📝 Full text: {full_text[:100]}...")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_temperature_variation(ollama_provider):
    """Тест: влияние температуры на генерацию."""
    messages = [
        Message(role="user", content="Скажи одно слово: привет или здравствуй")
    ]
    
    # Низкая температура (детерминированный)
    response_low = await ollama_provider.generate(messages, temperature=0.1, max_tokens=10)
    
    # Высокая температура (креативный)
    response_high = await ollama_provider.generate(messages, temperature=1.5, max_tokens=10)
    
    assert response_low.text is not None
    assert response_high.text is not None
    
    print(f"\n🔵 Low temp (0.1): {response_low.text}")
    print(f"🔴 High temp (1.5): {response_high.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_max_tokens_limit(ollama_provider):
    """Тест: ограничение max_tokens."""
    messages = [
        Message(role="user", content="Расскажи длинную историю о путешествии.")
    ]
    
    response = await ollama_provider.generate(messages, temperature=0.7, max_tokens=20)
    
    # Токенов не должно быть больше, чем max_tokens
    assert response.tokens_count <= 20, f"Token count {response.tokens_count} exceeds max_tokens=20"
    
    print(f"\n✅ Generated {response.tokens_count} tokens (max: 20)")
    print(f"📝 Text: {response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_russian_language(ollama_provider):
    """Тест: поддержка русского языка."""
    messages = [
        Message(role="user", content="Переведи на русский: Hello, how are you?")
    ]
    
    response = await ollama_provider.generate(messages, temperature=0.5, max_tokens=50)
    
    # Проверить, что в ответе есть кириллица
    has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in response.text)
    assert has_cyrillic, "Response should contain Cyrillic characters"
    
    print(f"\n✅ Russian response: {response.text}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_error_handling_empty_messages(ollama_provider):
    """Тест: обработка ошибки при пустых сообщениях."""
    with pytest.raises(ValueError, match="messages list cannot be empty"):
        await ollama_provider.generate([], temperature=0.7, max_tokens=100)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_error_handling_invalid_temperature(ollama_provider):
    """Тест: обработка ошибки при неправильной температуре."""
    messages = [Message(role="user", content="Test")]
    
    with pytest.raises(ValueError, match="temperature must be between"):
        await ollama_provider.generate(messages, temperature=3.0, max_tokens=100)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ollama_error_handling_invalid_max_tokens(ollama_provider):
    """Тест: обработка ошибки при неправильном max_tokens."""
    messages = [Message(role="user", content="Test")]
    
    with pytest.raises(ValueError, match="max_tokens must be between"):
        await ollama_provider.generate(messages, temperature=0.7, max_tokens=5000)

