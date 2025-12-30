"""Тесты для TTSFactory."""

from unittest.mock import Mock

import pytest

from avatar.config.settings import TTSConfig
from avatar.tts.factory import TTSFactory
from avatar.tts.silero_engine import SileroEngine


def test_create_silero():
    """Проверяем создание Silero."""
    # Используем правильную структуру конфига (Pydantic model)
    # Если TTSConfig требует обязательных полей, укажите их
    cfg = TTSConfig(engine="silero", language="ru")

    engine = TTSFactory.create(cfg)
    assert isinstance(engine, SileroEngine)
    assert engine.language == "ru"


def test_create_unknown_mock():
    # Создаем фейковый конфиг, обходя валидацию Pydantic
    fake_config = Mock()
    fake_config.engine = "unknown_thing"
    fake_config.language = "ru"

    with pytest.raises(ValueError):
        TTSFactory.create(fake_config)
