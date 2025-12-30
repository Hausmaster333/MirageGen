"""Тесты для PresetMotionGenerator."""

import json
import pathlib

import pytest

from avatar.motion.preset_loader import PresetMotionGenerator
from avatar.schemas.animation_types import MotionKeyframe, MotionKeyframes


@pytest.fixture
def temp_animations_dir(tmp_path):
    """Создать временную директорию с preset-анимациями."""
    animations_dir = tmp_path / "animations"
    animations_dir.mkdir()

    # Создаем preset файлы
    presets = {
        "idle": {
            "keyframes": [
                {
                    "timestamp": 0.0,
                    "bone_rotations": {"spine": [0.0, 0.0, 0.0, 1.0]},
                    "bone_positions": {"root": [0.0, 0.0, 0.0]},
                },
                {
                    "timestamp": 0.5,
                    "bone_rotations": {"spine": [0.0, 0.1, 0.0, 0.995]},
                    "bone_positions": {"root": [0.0, 0.0, 0.0]},
                },
            ],
            "emotion": "neutral",
            "duration": 1.0,
        },
        "happy_gesture": {
            "keyframes": [
                {
                    "timestamp": 0.0,
                    "bone_rotations": {"left_arm": [0.0, 0.0, 0.0, 1.0]},
                    "bone_positions": {},
                },
                {
                    "timestamp": 0.3,
                    "bone_rotations": {"left_arm": [0.0, 0.5, 0.0, 0.866]},
                    "bone_positions": {},
                },
            ],
            "emotion": "happy",
            "duration": 0.6,
        },
        "sad_gesture": {
            "keyframes": [
                {
                    "timestamp": 0.0,
                    "bone_rotations": {"head": [0.0, 0.0, 0.0, 1.0]},
                    "bone_positions": {},
                },
            ],
            "emotion": "sad",
            "duration": 0.5,
        },
        "thinking_gesture": {
            "keyframes": [
                {
                    "timestamp": 0.0,
                    "bone_rotations": {"head": [0.1, 0.0, 0.0, 0.995]},
                    "bone_positions": {},
                },
            ],
            "emotion": "thinking",
            "duration": 0.8,
        },
    }

    for preset_name, preset_data in presets.items():
        preset_file = animations_dir / f"{preset_name}.json"
        with pathlib.Path(preset_file).open("w", encoding="utf-8") as f:
            json.dump(preset_data, f)

    return animations_dir


@pytest.fixture
def mock_motion(temp_animations_dir):
    """Фикстура PresetMotionGenerator с временной директорией."""
    return PresetMotionGenerator(
        animations_dir=temp_animations_dir,
        fallback_action="idle",
    )


@pytest.mark.asyncio
async def test_motion_generate_happy(mock_motion):
    """Тест генерации motion для эмоции happy."""
    motion = await mock_motion.generate_motion("happy", duration=2.0)
    assert motion.emotion == "happy"
    assert motion.duration == 2.0
    assert len(motion.keyframes) > 0
    assert all(isinstance(kf, MotionKeyframe) for kf in motion.keyframes)


@pytest.mark.asyncio
async def test_motion_generate_all_emotions(mock_motion):
    """Тест генерации motion для всех поддерживаемых эмоций."""
    emotions = ["happy", "sad", "neutral", "thinking"]
    for emotion in emotions:
        motion = await mock_motion.generate_motion(emotion, duration=1.5)
        assert motion.emotion == emotion
        assert motion.duration == 1.5
        assert len(motion.keyframes) > 0


@pytest.mark.asyncio
async def test_motion_generate_with_action_hint(mock_motion):
    """Тест генерации motion с подсказкой действия."""
    motion = await mock_motion.generate_motion("happy", duration=1.0, action_hint="gesture")
    assert motion.emotion == "happy"
    assert motion.duration == 1.0


@pytest.mark.asyncio
async def test_motion_generate_invalid_emotion(mock_motion):
    """Тест генерации motion с невалидной эмоцией."""
    with pytest.raises(ValueError, match="Unsupported emotion"):
        await mock_motion.generate_motion("angry", duration=1.0)


@pytest.mark.asyncio
async def test_motion_generate_invalid_duration(mock_motion):
    """Тест генерации motion с невалидной длительностью."""
    with pytest.raises(ValueError, match="Duration must be positive"):
        await mock_motion.generate_motion("happy", duration=0.0)

    with pytest.raises(ValueError, match="Duration must be positive"):
        await mock_motion.generate_motion("happy", duration=-1.0)


@pytest.mark.asyncio
async def test_motion_generate_duration_scaling(mock_motion):
    """Тест масштабирования длительности анимации."""
    # Загружаем preset с оригинальной длительностью 0.6
    motion1 = await mock_motion.generate_motion("happy", duration=0.6)
    # Масштабируем до 1.2 (в 2 раза)
    motion2 = await mock_motion.generate_motion("happy", duration=1.2)

    assert motion1.duration == 0.6
    assert motion2.duration == 1.2
    assert len(motion1.keyframes) == len(motion2.keyframes)

    # Проверяем масштабирование timestamps
    for kf1, kf2 in zip(motion1.keyframes, motion2.keyframes, strict=False):
        assert abs(kf2.timestamp - kf1.timestamp * 2.0) < 0.01


@pytest.mark.asyncio
async def test_motion_generate_caching(mock_motion):
    """Тест кэширования preset-анимаций."""
    # Первый вызов загружает preset
    motion1 = await mock_motion.generate_motion("happy", duration=1.0)

    # Второй вызов должен использовать кэш
    motion2 = await mock_motion.generate_motion("happy", duration=2.0)

    # Keyframes из кэша, но timestamps масштабированы
    assert len(motion1.keyframes) == len(motion2.keyframes)
    assert motion2.duration == 2.0


def test_motion_available_actions(mock_motion):
    """Тест списка доступных действий."""
    actions = mock_motion.get_available_actions()
    assert "idle" in actions
    assert "happy_gesture" in actions
    assert "sad_gesture" in actions
    assert "thinking_gesture" in actions
    assert len(actions) == 4
    assert actions == sorted(actions)  # Проверка сортировки


def test_motion_load_preset(mock_motion):
    """Тест загрузки preset-анимации."""
    preset = mock_motion._load_preset("idle")
    assert isinstance(preset, MotionKeyframes)
    assert preset.emotion == "neutral"
    assert len(preset.keyframes) == 2
    assert preset.keyframes[0].timestamp == 0.0


def test_motion_load_preset_missing_file(mock_motion):
    """Тест загрузки несуществующего preset."""
    with pytest.raises(FileNotFoundError, match="Preset file not found"):
        mock_motion._load_preset("nonexistent")


def test_motion_load_preset_invalid_json(temp_animations_dir):
    """Тест загрузки preset с невалидным JSON."""
    invalid_file = temp_animations_dir / "invalid.json"
    with pathlib.Path(invalid_file).open("w") as f:
        f.write("{invalid json")

    generator = PresetMotionGenerator(animations_dir=temp_animations_dir)
    with pytest.raises(ValueError, match="Invalid JSON"):
        generator._load_preset("invalid")


def test_motion_load_preset_missing_required_field(temp_animations_dir):
    """Тест загрузки preset с отсутствующими обязательными полями."""
    broken_file = temp_animations_dir / "broken.json"
    with pathlib.Path(broken_file).open("w") as f:
        json.dump({"keyframes": [], "duration": 1.0}, f)  # Missing 'emotion'

    generator = PresetMotionGenerator(animations_dir=temp_animations_dir)
    with pytest.raises(ValueError, match="Missing required field"):
        generator._load_preset("broken")


def test_motion_map_emotion_to_preset(mock_motion):
    """Тест маппинга эмоций на preset."""
    assert mock_motion._map_emotion_to_preset("happy", None) == "happy_gesture"
    assert mock_motion._map_emotion_to_preset("sad", None) == "sad_gesture"
    assert mock_motion._map_emotion_to_preset("neutral", None) == "idle"
    assert mock_motion._map_emotion_to_preset("thinking", None) == "thinking_gesture"
    assert mock_motion._map_emotion_to_preset("unknown", None) == "idle"  # fallback


@pytest.mark.asyncio
async def test_motion_fallback_mechanism(temp_animations_dir):
    """Тест механизма fallback при ошибке загрузки preset."""
    # Удаляем happy_gesture preset
    (temp_animations_dir / "happy_gesture.json").unlink()

    generator = PresetMotionGenerator(
        animations_dir=temp_animations_dir,
        fallback_action="idle",
    )

    # Должен использовать fallback (idle)
    motion = await generator.generate_motion("happy", duration=1.0)

    # Эмоция из исходного запроса сохраняется
    assert motion.emotion == "happy"
    assert motion.duration == 1.0
    assert len(motion.keyframes) > 0  # Загружены keyframes из idle


@pytest.mark.asyncio
async def test_motion_fallback_fails(temp_animations_dir):
    """Тест когда fallback тоже не работает."""
    # Удаляем все preset файлы
    for json_file in temp_animations_dir.glob("*.json"):
        json_file.unlink()

    generator = PresetMotionGenerator(
        animations_dir=temp_animations_dir,
        fallback_action="idle",
    )

    with pytest.raises(RuntimeError, match="Failed to load fallback preset"):
        await generator.generate_motion("happy", duration=1.0)


def test_motion_init_missing_directory(tmp_path):
    """Тест инициализации с несуществующей директорией."""
    nonexistent_dir = tmp_path / "nonexistent"
    with pytest.raises(FileNotFoundError, match="Animations directory not found"):
        PresetMotionGenerator(animations_dir=nonexistent_dir)


def test_motion_scale_duration(mock_motion):
    """Тест метода масштабирования длительности."""
    # Загружаем preset
    original = mock_motion._load_preset("happy_gesture")

    # Масштабируем в 2 раза
    scaled = mock_motion._scale_duration(original, original.duration * 2)

    assert scaled.duration == original.duration * 2
    assert scaled.emotion == original.emotion
    assert len(scaled.keyframes) == len(original.keyframes)

    # Проверяем масштабирование timestamps
    for orig_kf, scaled_kf in zip(original.keyframes, scaled.keyframes, strict=False):
        assert abs(scaled_kf.timestamp - orig_kf.timestamp * 2) < 0.01


def test_motion_scale_duration_zero(mock_motion):
    """Тест масштабирования с нулевой исходной длительностью."""
    # Создаем motion с нулевой длительностью
    motion = MotionKeyframes(
        keyframes=[],
        emotion="neutral",
        duration=0.0,
    )

    # Масштабирование не должно изменять motion
    scaled = mock_motion._scale_duration(motion, 5.0)
    assert scaled.duration == 0.0


def test_motion_available_actions_empty_directory(tmp_path):
    """Тест get_available_actions с пустой директорией."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    generator = PresetMotionGenerator(animations_dir=empty_dir)
    actions = generator.get_available_actions()

    assert actions == []


def test_motion_preset_caching(mock_motion):
    """Тест что preset действительно кэшируется."""
    # Первая загрузка
    preset1 = mock_motion._load_preset("idle")

    # Вторая загрузка должна вернуть тот же объект из кэша
    preset2 = mock_motion._load_preset("idle")

    assert preset1 is preset2  # Тот же объект в памяти
