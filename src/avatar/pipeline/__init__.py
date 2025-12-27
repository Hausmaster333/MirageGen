# === Файл: src/avatar/pipeline/__init__.py ===
"""Pipeline orchestrator и streaming manager."""

from __future__ import annotations

from avatar.pipeline.avatar_pipeline import AvatarPipeline
from avatar.pipeline.streaming_manager import StreamingManager

__all__ = ["AvatarPipeline", "StreamingManager"]
