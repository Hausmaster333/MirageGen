# === Файл: src/avatar/api/__init__.py ===
"""FastAPI application и routes."""

from __future__ import annotations

from avatar.api.app import create_app

__all__ = ["create_app"]
