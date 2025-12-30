# === Файл: src/avatar/motion/preset_loader.py ===
"""Preset Motion Loader (загрузка preset-анимаций из JSON).

Используется для быстрой генерации motion на основе emotion-лейблов.
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from avatar.interfaces.motion import IMotionGenerator
from avatar.schemas.animation_types import MotionKeyframe, MotionKeyframes


class PresetMotionGenerator(IMotionGenerator):
    """Preset Motion Generator (загрузка JSON-анимаций).

    Attributes:
        animations_dir: Директория с preset-анимациями (idle.json, happy_gesture.json, ...).
        fallback_action: Дефолтное действие при ошибке.
        presets: Кэш загруженных preset-анимаций.
    """

    def __init__(
        self,
        animations_dir: Path = Path("assets/animations"),
        fallback_action: str = "idle",
    ) -> None:
        """Инициализация PresetMotionGenerator.

        Args:
            animations_dir: Директория с preset JSON.
            fallback_action: Дефолтное действие при ошибке.

        Raises:
            FileNotFoundError: Если animations_dir не существует.
        """
        if not animations_dir.exists():
            msg = f"Animations directory not found: {animations_dir}"
            raise FileNotFoundError(msg)
        self.animations_dir = animations_dir
        self.fallback_action = fallback_action
        self._presets: dict[str, MotionKeyframes] = {}
        logger.info(f"PresetMotionGenerator initialized: animations_dir={animations_dir}")

    async def generate_motion(
        self,
        emotion: str,
        duration: float,
        action_hint: str | None = None,
    ) -> MotionKeyframes:
        """Генерация motion-keyframes на основе эмоции.

        Args:
            emotion: Эмоция ("happy", "sad", "neutral", "thinking").
            duration: Длительность анимации в секундах.
            action_hint: Опциональная подсказка действия (например, "gesture").

        Returns:
            MotionKeyframes: Keyframes скелетной анимации.

        Raises:
            ValueError: Если эмоция не поддерживается.
            RuntimeError: Если загрузка preset не удалась.
        """
        # Валидация входных данных
        if duration <= 0:
            msg = f"Duration must be positive, got: {duration}"
            raise ValueError(msg)

        valid_emotions = {"happy", "sad", "neutral", "thinking"}
        if emotion not in valid_emotions:
            msg = f"Unsupported emotion: {emotion}. Valid emotions: {valid_emotions}"
            raise ValueError(msg)

        logger.debug(f"Generating motion: emotion={emotion}, duration={duration}, action_hint={action_hint}")

        # Маппинг эмоции на preset
        preset_name = self._map_emotion_to_preset(emotion, action_hint)

        try:
            # Загрузка preset
            motion = self._load_preset(preset_name)

            # Масштабирование длительности если необходимо
            if abs(motion.duration - duration) > 0.01:
                motion = self._scale_duration(motion, duration)

            logger.info(f"Motion generated: preset={preset_name}, keyframes={len(motion.keyframes)}")
            return motion

        except FileNotFoundError:
            logger.warning(f"Preset {preset_name} not found, trying fallback: {self.fallback_action}")
            try:
                fallback_motion = self._load_preset(self.fallback_action)
                return self._scale_duration(fallback_motion, duration)
            except Exception as e:
                msg = f"Failed to load fallback preset {self.fallback_action}: {e}"
                raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to generate motion: {e}"
            raise RuntimeError(msg) from e

    def get_available_actions(self) -> list[str]:
        """Список доступных действий/preset.

        Returns:
            list[str]: Имена preset (например, ["idle", "happy_gesture", "thinking_gesture"]).
        """
        # Сканируем директорию для JSON файлов
        try:
            json_files = list(self.animations_dir.glob("*.json"))
            actions = [f.stem for f in json_files]
            logger.debug(f"Available actions: {actions}")
            return sorted(actions)
        except Exception as e:
            logger.error(f"Failed to scan animations directory: {e}")
            return []

    def _load_preset(self, preset_name: str) -> MotionKeyframes:
        """Загрузить preset-анимацию из JSON.

        Args:
            preset_name: Имя preset (например, "idle").

        Returns:
            MotionKeyframes: Загруженные keyframes.

        Raises:
            FileNotFoundError: Если файл preset не найден.
            ValueError: Если JSON невалиден.
        """
        # Проверка кэша
        if preset_name in self._presets:
            logger.debug(f"Loading preset from cache: {preset_name}")
            return self._presets[preset_name]

        # Путь к файлу
        preset_path = self.animations_dir / f"{preset_name}.json"

        if not preset_path.exists():
            msg = f"Preset file not found: {preset_path}"
            raise FileNotFoundError(msg)

        try:
            logger.debug(f"Loading preset from file: {preset_path}")
            with Path(preset_path).open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Парсинг keyframes
            keyframes = []
            for kf_data in data.get("keyframes", []):
                keyframe = MotionKeyframe(
                    timestamp=kf_data["timestamp"],
                    bone_rotations=kf_data.get("bone_rotations", {}),
                    bone_positions=kf_data.get("bone_positions", {}),
                )
                keyframes.append(keyframe)

            # Создание MotionKeyframes
            motion = MotionKeyframes(
                keyframes=keyframes,
                emotion=data["emotion"],
                duration=data["duration"],
            )

            # Кэширование
            self._presets[preset_name] = motion
            logger.info(f"Preset loaded: {preset_name} ({len(keyframes)} keyframes)")

            return motion

        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in preset file {preset_path}: {e}"
            raise ValueError(msg) from e
        except KeyError as e:
            msg = f"Missing required field in preset {preset_path}: {e}"
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Failed to load preset {preset_path}: {e}"
            raise ValueError(msg) from e

    def _map_emotion_to_preset(self, emotion: str, action_hint: str | None) -> str:
        """Маппинг эмоции → имя preset.

        Args:
            emotion: Эмоция.
            action_hint: Опциональная подсказка действия.

        Returns:
            str: Имя preset (например, "happy_gesture").
        """
        emotion_map = {
            "happy": "happy_gesture",
            "sad": "sad_gesture",
            "neutral": "idle",
            "thinking": "thinking_gesture",
        }
        return emotion_map.get(emotion, self.fallback_action)

    def _scale_duration(self, motion: MotionKeyframes, target_duration: float) -> MotionKeyframes:
        """Масштабировать длительность анимации.

        Args:
            motion: Исходная анимация.
            target_duration: Целевая длительность в секундах.

        Returns:
            MotionKeyframes: Масштабированная анимация.
        """
        if motion.duration == 0:
            return motion

        scale_factor = target_duration / motion.duration

        scaled_keyframes = []
        for kf in motion.keyframes:
            scaled_kf = MotionKeyframe(
                timestamp=kf.timestamp * scale_factor,
                bone_rotations=kf.bone_rotations.copy(),
                bone_positions=kf.bone_positions.copy(),
            )
            scaled_keyframes.append(scaled_kf)

        return MotionKeyframes(
            keyframes=scaled_keyframes,
            emotion=motion.emotion,
            duration=target_duration,
        )
