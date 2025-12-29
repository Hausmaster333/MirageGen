"""Тесты для audio_utils."""
import io
from pathlib import Path
from avatar.schemas.audio_types import AudioSegment
from avatar.tts.audio_utils import save_audio_segment, normalize_audio
import io
import wave


def create_dummy_wav_bytes():
    """Создает валидные байты WAV файла (тишина)."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16 bit
        wav_file.setframerate(24000)
        wav_file.writeframes(b'\x00\x00' * 100)  # немного тишины
    return buf.getvalue()


def test_load_audio(tmp_path):
    wav_bytes = create_dummy_wav_bytes()
    p = tmp_path / "test.wav"
    p.write_bytes(wav_bytes)

    # Тестируем загрузку
    from avatar.tts.audio_utils import load_audio_segment
    seg = load_audio_segment(p)
    assert seg.sample_rate == 24000
    assert seg.duration > 0


def test_normalize_success():
    wav_bytes = create_dummy_wav_bytes()
    from avatar.tts.audio_utils import normalize_audio
    res = normalize_audio(wav_bytes)
    assert len(res) > 0
    assert res != b"invalid"  # Должен вернуть валидный wav


def test_save_audio(tmp_path):
    """Тест сохранения."""
    audio = AudioSegment(
        audio_bytes=b"fake",
        sample_rate=24000,
        format="wav",
        duration=1.0
    )
    path = tmp_path / "test.wav"
    save_audio_segment(audio, path)

    assert path.exists()
    assert path.read_bytes() == b"fake"


def test_normalize():
    """Тест (простой прогон, так как внутри pydub)."""
    # Создаем минимальный валидный WAV заголовок + данные, чтобы pydub не упал
    # Или просто проверяем, что функция не падает на мусоре (если там есть try/except)
    fake_wav = b"RIFF....WAVEfmt ...."  # Сложно создать вручную

    # Проще проверить обработку ошибок:
    res = normalize_audio(b"invalid_bytes")
    # Она должна вернуть исходные байты при ошибке (согласно нашему коду)
    assert res == b"invalid_bytes"
