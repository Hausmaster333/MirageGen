# """Тесты для SileroEngine (с mock)."""
#
# import pytest
#
# @pytest.mark.asyncio
# async def test_silero_synthesize(mock_tts):
#     """Тест синтеза Silero TTS."""
#     # Используем фикстуру mock_tts (она должна быть настроена в conftest.py)
#     # или создаем инстанс SileroEngine с замоканным torch.hub.load
#
#     audio = await mock_tts.synthesize("Привет!")
#
#     assert audio.audio_bytes == b"fake_audio"
#     assert audio.sample_rate == 48000  # V5 работает на 48k
#     assert audio.format == "wav"
#     assert audio.duration > 0.0
#
# @pytest.mark.asyncio
# async def test_silero_stream(mock_tts):
#     """Тест стриминга Silero TTS (через генератор предложений)."""
#     chunks = []
#     async for chunk in mock_tts.synthesize_streaming("Тест. Проверка."):
#         chunks.append(chunk)
#
#     assert len(chunks) > 0
#     assert chunks[0].audio_bytes == b"fake_chunk"
#
# def test_silero_supported_languages(mock_tts):
#     """Тест списка поддерживаемых языков."""
#     languages = mock_tts.get_supported_languages()
#     assert "ru" in languages
#     assert len(languages) == 1  # Silero V5 настроен только на ru
"""Тесты для реального SileroEngine с mock (безопасный вариант)."""
import pytest
from unittest.mock import MagicMock, patch
import torch

from avatar.tts.silero_engine import SileroEngine

# 1. Создаем фейковую модель (имитация нейросети)
class MockSileroModel(torch.nn.Module):
    def apply_tts(self, text, speaker, sample_rate):
        # Возвращаем 1 секунду тишины/шума
        return torch.zeros(48000)

    def to(self, device):
        return self

# 2. Фикстура с "безопасным" движком
@pytest.fixture
def real_engine_mocked():
    """Возвращает SileroEngine, у которого ЗАБЛОКИРОВАН выход в интернет."""

    # Патчим метод _load_model прямо в классе SileroEngine
    # Это гарантирует, что torch.hub.load вообще не будет вызван
    with patch.object(SileroEngine, "_load_model") as mock_method:

        # Настраиваем, чтобы этот метод возвращал нашу фейковую модель
        mock_model = MockSileroModel()
        mock_method.return_value = mock_model

        # Инициализируем движок
        engine = SileroEngine(language="ru", speaker="xenia", sample_rate=48000)

        # Важно: так как _load_model теперь мок, он не запишет модель в self._model сам.
        # Сделаем это вручную для надежности тестов, если логика класса полагается на self._model
        engine._model = mock_model

        yield engine

# 3. Сами тесты

@pytest.mark.asyncio
async def test_real_synthesize(real_engine_mocked):
    """Проверяем метод synthesize."""
    # Этот вызов пойдет в реальный метод synthesize,
    # но вместо скачивания вызовет наш мок _load_model
    audio = await real_engine_mocked.synthesize("Привет")

    assert audio.sample_rate == 48000
    assert audio.format == "wav"
    assert len(audio.audio_bytes) > 0
    assert audio.duration == 1.0  # 48000 семплов / 48000 rate

@pytest.mark.asyncio
async def test_real_stream(real_engine_mocked):
    """Проверяем стриминг."""
    chunks = []
    async for chunk in real_engine_mocked.synthesize_streaming("Раз. Два."):
        chunks.append(chunk)

    assert len(chunks) >= 2

def test_initialization_error():
    """Проверяем валидацию языка."""
    with pytest.raises(ValueError):
        SileroEngine(language="en")

@pytest.mark.asyncio
async def test_empty_text_error(real_engine_mocked):
    with pytest.raises(ValueError):
        await real_engine_mocked.synthesize("")


@patch("torch.hub.load")
def test_load_model_logic(mock_hub_load):
    """Проверяем логику внутри _load_model (ленивая загрузка)."""
    # Настраиваем мок хаба
    mock_model = MagicMock()
    mock_hub_load.return_value = (mock_model, None)

    # Создаем движок (без патча _load_model!)
    engine = SileroEngine(language="ru", speaker="xenia")

    # 1. Первый вызов - должен загрузить
    model1 = engine._load_model()
    assert model1 == mock_model
    mock_hub_load.assert_called_once()

    # 2. Второй вызов - должен вернуть кэшированное (не вызывать хаб снова)
    model2 = engine._load_model()
    assert model2 == mock_model
    mock_hub_load.assert_called_once()  # Счетчик вызовов не изменился
