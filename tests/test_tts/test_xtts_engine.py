"""Тесты для XTTSEngine (с mock)."""

import pytest


@pytest.mark.asyncio
async def test_tts_synthesize(mock_tts):
    """Тест синтеза TTS."""
    audio = await mock_tts.synthesize("Привет!")
    
    assert audio.audio_bytes == b"fake_audio"
    assert audio.sample_rate == 24000
    assert audio.format == "wav"
    assert audio.duration > 0.0


@pytest.mark.asyncio
async def test_tts_stream(mock_tts):
    """Тест стриминга TTS."""
    chunks = []
    async for chunk in mock_tts.synthesize_streaming("Тест"):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert chunks[0].audio_bytes == b"fake_chunk"


def test_tts_supported_languages(mock_tts):
    """Тест списка поддерживаемых языков."""
    languages = mock_tts.get_supported_languages()
    assert "ru" in languages
    assert "en" in languages
