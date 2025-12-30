"""Тесты для реального SileroEngine с mock (безопасный вариант)."""

from unittest.mock import MagicMock, patch

import pytest
import torch

from avatar.tts.silero_engine import SileroEngine


# 1. Фейковая модель
class MockSileroModel(torch.nn.Module):
    def apply_tts(self, text, speaker, sample_rate):
        return torch.zeros(48000)

    def to(self, device):
        return self


# 2. Фикстура с "безопасным" движком (блокирует _load_model целиком)
@pytest.fixture
def real_engine_mocked():
    with patch.object(SileroEngine, "_load_model") as mock_method:
        mock_model = MockSileroModel()
        mock_method.return_value = mock_model

        engine = SileroEngine(language="ru", speaker="xenia", sample_rate=48000)
        engine._model = mock_model

        yield engine


# 3. Тесты синтеза (используют фикстуру)
@pytest.mark.asyncio
async def test_real_synthesize(real_engine_mocked):
    audio = await real_engine_mocked.synthesize("Привет")
    assert audio.sample_rate == 48000
    assert audio.format == "wav"
    assert len(audio.audio_bytes) > 0


@pytest.mark.asyncio
async def test_real_stream(real_engine_mocked):
    chunks = []
    async for chunk in real_engine_mocked.synthesize_streaming("Раз. Два."):
        chunks.append(chunk)
    assert len(chunks) >= 2


def test_initialization_error():
    with pytest.raises(ValueError):
        SileroEngine(language="en")


@pytest.mark.asyncio
async def test_empty_text_error(real_engine_mocked):
    with pytest.raises(ValueError):
        await real_engine_mocked.synthesize("")


# 4. ТЕСТ ЗАГРУЗКИ МОДЕЛИ (исправленный)
# Мокаем download_url_to_file (чтобы не качал) и PackageImporter (чтобы не грузил)
@patch("torch.hub.download_url_to_file")
@patch("torch.package.PackageImporter")
def test_load_model_logic(mock_importer, mock_download):
    """Проверяем логику внутри _load_model (скачивание и загрузка)."""

    # Настраиваем моки
    mock_model_package = MagicMock()
    mock_loaded_model = MagicMock()

    # Цепочка: Importer(...) -> load_pickle(...) -> модель
    mock_importer.return_value = mock_model_package
    mock_model_package.load_pickle.return_value = mock_loaded_model

    # Создаем движок (тут _load_model реальный!)
    engine = SileroEngine(language="ru", speaker="xenia")

    # === Сценарий 1: Модели нет локально ===
    with patch("pathlib.Path.exists", return_value=False):
        model1 = engine._load_model()

        # Проверяем, что пытался скачать
        mock_download.assert_called_once()
        # Проверяем, что загрузил через PackageImporter
        assert model1 == mock_loaded_model
        assert engine._model == mock_loaded_model

    # Сбрасываем моки для второго теста
    mock_download.reset_mock()
    mock_importer.reset_mock()
    engine._model = None  # сбрасываем кэш внутри класса

    # === Сценарий 2: Модель уже есть локально ===
    with patch("pathlib.Path.exists", return_value=True):
        model2 = engine._load_model()

        # НЕ должен качать
        mock_download.assert_not_called()
        # Должен загрузить
        mock_importer.assert_called_once()
        assert model2 == mock_loaded_model


@pytest.mark.asyncio
async def test_stream_with_spaces(real_engine_mocked):
    """Проверяем стриминг."""
    # Используем строку, где между предложениями просто много пробелов, без лишних точек
    # re.split(r'(?<=[.!?]) +') сработает на "Раз. " -> "Раз."
    # А вот "   " он может и не заметить, если там нет знака препинания перед ним.

    # Попробуем так: Предложение. <много пробелов> Предложение.
    input_text = "Раз.          Два."

    chunks = []
    async for chunk in real_engine_mocked.synthesize_streaming(input_text):
        chunks.append(chunk)

    # Должно быть 2 чанка: "Раз." и "Два."
    assert len(chunks) == 2


def test_get_languages(real_engine_mocked):
    """Тест для покрытия строки 125."""
    assert real_engine_mocked.get_supported_languages() == ["ru"]


@pytest.mark.asyncio
async def test_stream_skips_empty(real_engine_mocked):
    """Тест для покрытия строки 115 (пропуск пустот)."""
    # Текст заканчивается пробелом после точки -> re.split даст пустую строку в конце
    input_text = "Word. "

    chunks = []
    async for chunk in real_engine_mocked.synthesize_streaming(input_text):
        chunks.append(chunk)

    # Должен быть 1 чанк ("Word."), пустой хвост отброшен
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_synthesize_2d_tensor(real_engine_mocked):
    """Тест для покрытия строки 89 (сжатие размерности)."""
    # Подменяем метод apply_tts, чтобы он вернул [1, 48000]
    real_engine_mocked._model.apply_tts = MagicMock(return_value=torch.zeros(1, 48000))

    audio = await real_engine_mocked.synthesize("Тест")
    assert len(audio.audio_bytes) > 0
