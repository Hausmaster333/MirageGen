# === Файл: src/avatar/tts/__init__.py ===

from avatar.tts.factory import TTSFactory
from avatar.tts.silero_engine import SileroEngine

# XTTSEngine удален (почти)
# from avatar.tts.xtts_engine import XTTSEngine

__all__ = ["TTSFactory", "SileroEngine"]
