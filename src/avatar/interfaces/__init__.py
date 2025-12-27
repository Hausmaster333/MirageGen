"""Публичные интерфейсы (протоколы) для всех компонентов пайплайна."""

from __future__ import annotations

from avatar.interfaces.lipsync import ILipSyncGenerator
from avatar.interfaces.llm import ILLMProvider
from avatar.interfaces.motion import IMotionGenerator
from avatar.interfaces.pipeline import IPipeline
from avatar.interfaces.tts import ITTSEngine

__all__ = [
    "ILipSyncGenerator",
    "ILLMProvider",
    "IMotionGenerator",
    "IPipeline",
    "ITTSEngine",
]