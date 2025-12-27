"""Pytest fixtures для всех тестов."""

from __future__ import annotations

import pytest
from pathlib import Path

from avatar.config import Settings
from avatar.motion.sentiment_analyzer import SentimentAnalyzer
from avatar.pipeline.avatar_pipeline import AvatarPipeline


# ===== Mock-реализации =====

class MockLLMProvider:
    """Mock LLM для тестов."""
    
    async def generate(self, messages, temperature=0.7, max_tokens=512):
        from avatar.schemas.llm_types import LLMResponse
        return LLMResponse(
            text="Mock LLM response",
            action="happy",
            tokens_count=10,
            generation_time=0.1,
        )
    
    async def generate_stream(self, messages, temperature=0.7, max_tokens=512):
        for word in ["Mock", "stream", "response"]:
            yield word + " "
    
    async def healthcheck(self):
        return True


class MockTTSEngine:
    """Mock TTS для тестов."""
    
    async def synthesize(self, text, language="ru", speaker_wav=None):
        from avatar.schemas.audio_types import AudioSegment
        return AudioSegment(
            audio_bytes=b"fake_audio",
            sample_rate=24000,
            format="wav",
            duration=1.0,
        )
    
    async def synthesize_streaming(self, text, language="ru"):
        from avatar.schemas.audio_types import AudioSegment
        yield AudioSegment(
            audio_bytes=b"fake_chunk",
            sample_rate=24000,
            format="wav",
            duration=0.5,
        )
    
    def get_supported_languages(self):
        return ["ru", "en"]


class MockLipSyncGenerator:
    """Mock Lipsync для тестов."""
    
    async def generate_blendshapes(self, audio_path, recognizer="pocketSphinx"):
        from avatar.schemas.animation_types import BlendshapeWeights, BlendshapeFrame
        return BlendshapeWeights(
            frames=[
                BlendshapeFrame(timestamp=0.0, mouth_shapes={"viseme_aa": 0.8}),
            ],
            fps=30,
            duration=1.0,
        )
    
    def get_phoneme_mapping(self):
        return {"A": "viseme_aa", "B": "viseme_PP"}


class MockMotionGenerator:
    """Mock Motion для тестов."""
    
    async def generate_motion(self, emotion, duration, action_hint=None):
        from avatar.schemas.animation_types import MotionKeyframes, MotionKeyframe
        return MotionKeyframes(
            keyframes=[
                MotionKeyframe(
                    timestamp=0.0,
                    bone_rotations={"spine": (0.0, 0.0, 0.0, 1.0)},
                    bone_positions={},
                ),
            ],
            emotion=emotion,
            duration=duration,
        )
    
    def get_available_actions(self):
        return ["idle", "happy_gesture"]


# ===== Fixtures =====

@pytest.fixture
def mock_llm():
    """Фикстура для mock LLM."""
    return MockLLMProvider()


@pytest.fixture
def mock_tts():
    """Фикстура для mock TTS."""
    return MockTTSEngine()


@pytest.fixture
def mock_lipsync():
    """Фикстура для mock Lipsync."""
    return MockLipSyncGenerator()


@pytest.fixture
def mock_motion():
    """Фикстура для mock Motion."""
    return MockMotionGenerator()


@pytest.fixture
def mock_sentiment():
    """Фикстура для mock Sentiment."""
    return SentimentAnalyzer()


@pytest.fixture
def test_pipeline(mock_llm, mock_tts, mock_lipsync, mock_motion, mock_sentiment):
    """Фикстура для тестового pipeline."""
    return AvatarPipeline(
        llm_provider=mock_llm,
        tts_engine=mock_tts,
        lipsync_generator=mock_lipsync,
        motion_generator=mock_motion,
        sentiment_analyzer=mock_sentiment,
    )


@pytest.fixture
def test_settings():
    """Фикстура для тестовых настроек."""
    return Settings()


@pytest.fixture
def temp_audio_file(tmp_path):
    """Фикстура для временного аудио-файла."""
    audio_file = tmp_path / "test_audio.wav"
    audio_file.write_bytes(b"fake_audio_data")
    return audio_file
