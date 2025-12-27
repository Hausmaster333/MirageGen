"""Тесты для PresetMotionGenerator (с mock)."""

import pytest


@pytest.mark.asyncio
async def test_motion_generate(mock_motion):
    """Тест генерации motion."""
    motion = await mock_motion.generate_motion("happy", duration=1.0)
    
    assert motion.emotion == "happy"
    assert motion.duration == 1.0
    assert len(motion.keyframes) > 0


def test_motion_available_actions(mock_motion):
    """Тест списка доступных действий."""
    actions = mock_motion.get_available_actions()
    
    assert "idle" in actions
    assert "happy_gesture" in actions
