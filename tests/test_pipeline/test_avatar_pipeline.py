"""Тесты для AvatarPipeline."""

import pytest
from avatar.schemas.llm_types import Message


@pytest.mark.asyncio
async def test_pipeline_healthcheck(test_pipeline):
    """Тест healthcheck pipeline."""
    health = await test_pipeline.healthcheck()
    
    assert isinstance(health, dict)
    # Раскомментируйте после реализации healthcheck:
    # assert health["llm"] is True


@pytest.mark.asyncio
async def test_pipeline_process(test_pipeline):
    """Тест обработки через pipeline."""
    frames = []
    async for frame in test_pipeline.process("Привет!"):
        frames.append(frame)
    
    # Раскомментируйте после реализации process:
    # assert len(frames) > 0
    # assert frames[0].text_chunk is not None
