"""Комплексные тесты для AvatarPipeline."""

import pytest

from avatar.schemas.api_types import AvatarFrame


@pytest.mark.asyncio
async def test_pipeline_healthcheck(test_pipeline):
    """Тест healthcheck pipeline."""
    health = await test_pipeline.healthcheck()

    assert isinstance(health, dict)
    assert "llm" in health
    assert "tts" in health
    assert "lipsync" in health
    assert "motion" in health
    assert health["llm"] is True  # Mock всегда healthy


@pytest.mark.asyncio
async def test_pipeline_process_basic(test_pipeline):
    """Тест базовой обработки через pipeline."""
    frames = []
    async for frame in test_pipeline.process("Привет!"):
        frames.append(frame)

    # Должны получить фреймы (mock LLM возвращает 3 слова)
    assert len(frames) > 0

    # Проверяем структуру первого фрейма
    first_frame = frames[0]
    assert isinstance(first_frame, AvatarFrame)
    assert first_frame.timestamp >= 0.0
    assert first_frame.text_chunk is not None
    assert first_frame.audio_chunk is not None
    assert first_frame.blendshapes is not None
    assert first_frame.motion is not None


@pytest.mark.asyncio
async def test_pipeline_process_empty_input(test_pipeline):
    """Тест на пустой ввод."""
    with pytest.raises(ValueError, match="cannot be empty"):
        async for _ in test_pipeline.process(""):
            pass


@pytest.mark.asyncio
async def test_pipeline_process_long_input(test_pipeline):
    """Тест на слишком длинный ввод."""
    long_text = "a" * 2001
    with pytest.raises(ValueError, match="too long"):
        async for _ in test_pipeline.process(long_text):
            pass


@pytest.mark.asyncio
async def test_pipeline_process_with_history(test_pipeline):
    """Тест с историей диалога."""
    from avatar.schemas.llm_types import Message

    history = [
        Message(role="user", content="Привет"),
        Message(role="assistant", content="Здравствуйте!"),
    ]

    frames = []
    async for frame in test_pipeline.process("Как дела?", conversation_history=history):
        frames.append(frame)

    assert len(frames) > 0


@pytest.mark.asyncio
async def test_pipeline_frame_timestamps_monotonic(test_pipeline):
    """Тест монотонности таймстампов."""
    frames = []
    async for frame in test_pipeline.process("Test message"):
        frames.append(frame)

    # Таймстампы должны расти
    for i in range(1, len(frames)):
        assert frames[i].timestamp >= frames[i - 1].timestamp


@pytest.mark.asyncio
async def test_pipeline_blendshapes_format(test_pipeline):
    """Тест формата blendshapes."""
    frames = []
    async for frame in test_pipeline.process("Test"):
        frames.append(frame)

    assert len(frames) > 0
    first_frame = frames[0]

    # Blendshapes должны быть dict[str, float]
    assert isinstance(first_frame.blendshapes, dict)
    for key, value in first_frame.blendshapes.items():
        assert isinstance(key, str)
        assert isinstance(value, float)


@pytest.mark.asyncio
async def test_pipeline_motion_format(test_pipeline):
    """Тест формата motion."""
    frames = []
    async for frame in test_pipeline.process("Test"):
        frames.append(frame)

    assert len(frames) > 0
    first_frame = frames[0]

    # Motion должен быть dict[str, tuple[float, float, float, float]]
    assert isinstance(first_frame.motion, dict)
    for bone, quat in first_frame.motion.items():
        assert isinstance(bone, str)
        assert isinstance(quat, tuple)
        assert len(quat) == 4
        assert all(isinstance(x, float) for x in quat)
