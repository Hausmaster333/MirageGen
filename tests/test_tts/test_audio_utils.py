import io
import wave
import pytest
from pathlib import Path
from unittest.mock import patch
from avatar.schemas.audio_types import AudioSegment
from avatar.tts.audio_utils import (
    save_audio_segment,
    load_audio_segment,
    normalize_audio,
    convert_sample_rate
)
from unittest.mock import patch
from unittest.mock import MagicMock


def test_normalize_logic_mocked():
    """Тест успешной нормализации с моком Pydub."""
    # Мокаем класс PydubSegment
    with patch("avatar.tts.audio_utils.PydubSegment") as MockSegment:
        # Настраиваем мок инстанса сегмента
        mock_instance = MagicMock()
        mock_instance.dBFS = -10.0  # Текущая громкость

        # apply_gain возвращает новый (или тот же) сегмент
        mock_normalized = MagicMock()
        mock_instance.apply_gain.return_value = mock_normalized

        # from_wav возвращает наш инстанс
        MockSegment.from_wav.return_value = mock_instance

        # export записывает что-то в буфер
        def side_effect_export(buf, format):
            buf.write(b"normalized_audio")

        mock_normalized.export.side_effect = side_effect_export

        # Вызываем функцию
        from avatar.tts.audio_utils import normalize_audio
        result = normalize_audio(b"input_audio", target_db=-20.0)

        # Проверки
        assert result == b"normalized_audio"
        # Проверяем, что gain был вычислен верно: -20 - (-10) = -10
        mock_instance.apply_gain.assert_called_with(-10.0)


def test_normalize_exception():
    """Тест исключения внутри normalize_audio."""
    # Форсируем ошибку внутри pydub
    with patch("pydub.AudioSegment.from_wav", side_effect=Exception("Boom")):
        res = normalize_audio(b"any_bytes")
        # Должен вернуть исходные байты и не упасть
        assert res == b"any_bytes"

# Хелпер для создания валидного WAV
def create_wav_bytes(rate=24000):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        wav_file.writeframes(b'\x00\x00' * 100)
    return buf.getvalue()

# --- Тесты save_audio_segment ---

def test_save_audio_success(tmp_path):
    audio = AudioSegment(audio_bytes=b"fake", sample_rate=24000, format="wav", duration=1.0)
    path = tmp_path / "test.wav"
    save_audio_segment(audio, path)
    assert path.read_bytes() == b"fake"


def test_save_audio_invalid_format(tmp_path):
    audio = AudioSegment(audio_bytes=b"fake", sample_rate=24000, format="wav", duration=1.0)
    path = tmp_path / "test.txt"

    # Ожидаем IOError, так как функция оборачивает ValueError в него
    with pytest.raises(IOError, match="Unsupported format"):
        save_audio_segment(audio, path)


def test_save_audio_io_error(tmp_path):
    audio = AudioSegment(audio_bytes=b"fake", sample_rate=24000, format="wav", duration=1.0)
    # Пытаемся сохранить в директорию как в файл
    path = tmp_path

    with pytest.raises(IOError):
        save_audio_segment(audio, path)

# --- Тесты load_audio_segment ---

def test_load_audio_success(tmp_path):
    wav_bytes = create_wav_bytes()
    path = tmp_path / "in.wav"
    path.write_bytes(wav_bytes)

    seg = load_audio_segment(path)
    assert seg.sample_rate == 24000
    assert len(seg.audio_bytes) > 0

def test_load_audio_not_found():
    with pytest.raises(FileNotFoundError):
        load_audio_segment(Path("non_existent.wav"))

def test_load_audio_corrupted(tmp_path):
    path = tmp_path / "bad.wav"
    path.write_bytes(b"not a wav file")

    # pydub выбросит ошибку, мы ловим её и кидаем ValueError
    with pytest.raises(ValueError):
        load_audio_segment(path)

# --- Тесты convert_sample_rate ---

def test_convert_rate_same():
    b = b"data"
    # Если частоты совпадают, возвращает то же самое
    assert convert_sample_rate(b, 24000, 24000) == b

def test_convert_rate_success():
    # Реальная конвертация (требует ffmpeg)
    src = create_wav_bytes(24000)
    res = convert_sample_rate(src, 24000, 16000)
    assert res != src
    assert len(res) > 0

def test_convert_rate_error():
    # Передаем мусор, pydub должен упасть
    with pytest.raises(ValueError):
        convert_sample_rate(b"junk", 24000, 16000)

# --- Тесты normalize_audio ---

def test_normalize_error():
    # При ошибке возвращает исходные байты
    junk = b"junk"
    assert normalize_audio(junk) == junk
