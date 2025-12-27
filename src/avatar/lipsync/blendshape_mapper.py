# === Файл: src/avatar/lipsync/blendshape_mapper.py ===
"""Утилиты для mapping phonemes → blendshape names.

Используется для кастомных mapping (например, для разных 3D-моделей).
"""

from __future__ import annotations

from loguru import logger


DEFAULT_RHUBARB_MAPPING = {
    "A": "viseme_aa",
    "B": "viseme_PP",
    "C": "viseme_E",
    "D": "viseme_aa",
    "E": "viseme_O",
    "F": "viseme_FF",
    "G": "viseme_TH",
    "H": "viseme_DD",
    "X": "viseme_sil",
}


def get_rhubarb_mapping(custom_mapping: dict[str, str] | None = None) -> dict[str, str]:
    """Получить phoneme mapping (дефолтный или кастомный).

    Args:
        custom_mapping: Опциональный кастомный mapping.

    Returns:
        dict[str, str]: Phoneme mapping.
    """
    if custom_mapping:
        logger.info("Using custom phoneme mapping")
        return custom_mapping
    return DEFAULT_RHUBARB_MAPPING


def remap_blendshapes(
    frames: list[dict[str, float]],
    mapping: dict[str, str],
) -> list[dict[str, float]]:
    """Переименовать phoneme-ключи в blendshape-имена.

    Args:
        frames: Список кадров с phoneme-ключами (например, [{"A": 0.8, "B": 0.2}, ...]).
        mapping: Mapping phoneme → blendshape name.

    Returns:
        list[dict[str, float]]: Кадры с переименованными ключами.

    Raises:
        ValueError: Если phoneme не найдена в mapping.
    """
    raise NotImplementedError("TODO: Implement remap_blendshapes")
