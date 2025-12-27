# === Файл: src/avatar/schemas/animationtypes.py ===
"""Pydantic-модели данных анимации (липсинк и motion).

Содержит структуры для blendshape-кадров и keyframes скелета, как это задано в SPEC.md.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BlendshapeFrame(BaseModel):
    """Один кадр blendshape (viseme) анимации.

    Attributes:
        timestamp: Время кадра в секундах от начала сегмента.
        mouth_shapes: Словарь весов форм рта (viseme -> weight).
    """

    timestamp: float = Field(..., ge=0.0, description="Frame timestamp (seconds).")
    mouth_shapes: dict[str, float] = Field(
        default_factory=dict,
        description="Blendshape weights mapping (name -> weight).",
    )


class BlendshapeWeights(BaseModel):
    """Набор blendshape-кадров на интервале аудио.

    Attributes:
        frames: Список кадров blendshape.
        fps: Частота кадров.
        duration: Длительность сегмента в секундах.
    """

    frames: list[BlendshapeFrame] = Field(default_factory=list, description="Blendshape frames.")
    fps: int = Field(default=30, ge=1, description="Frames per second.")
    duration: float = Field(..., ge=0.0, description="Duration in seconds.")


class MotionKeyframe(BaseModel):
    """Один ключевой кадр скелетной анимации.

    Attributes:
        timestamp: Время кадра в секундах от начала сегмента.
        bone_rotations: Кватернионы поворота костей (bone -> (x, y, z, w)).
        bone_positions: Позиции костей (bone -> (x, y, z)).
    """

    timestamp: float = Field(..., ge=0.0, description="Keyframe timestamp (seconds).")
    bone_rotations: dict[str, tuple[float, float, float, float]] = Field(
        default_factory=dict,
        description="Bone rotations as quaternions (x, y, z, w).",
    )
    bone_positions: dict[str, tuple[float, float, float]] = Field(
        default_factory=dict,
        description="Bone positions (x, y, z).",
    )


class MotionKeyframes(BaseModel):
    """Набор keyframes для motion/gesture анимации.

    Attributes:
        keyframes: Список ключевых кадров.
        emotion: Эмоциональная метка (happy/sad/neutral/thinking).
        duration: Длительность анимации в секундах.
    """

    keyframes: list[MotionKeyframe] = Field(default_factory=list, description="Motion keyframes.")
    emotion: Literal["happy", "sad", "neutral", "thinking"] = Field(
        ...,
        description="Emotion label.",
    )
    duration: float = Field(..., ge=0.0, description="Duration in seconds.")
