"""Тесты для RhubarbGenerator (с mock)."""

import pytest


@pytest.mark.asyncio
async def test_lipsync_generate_blendshapes(mock_lipsync, temp_audio_file):
    """Тест генерации blendshapes."""
    blendshapes = await mock_lipsync.generate_blendshapes(temp_audio_file)

    assert len(blendshapes.frames) > 0
    assert blendshapes.fps == 30
    assert blendshapes.duration > 0.0


def test_lipsync_phoneme_mapping(mock_lipsync):
    """Тест phoneme mapping."""
    mapping = mock_lipsync.get_phoneme_mapping()

    assert "A" in mapping
    assert mapping["A"] == "viseme_aa"
