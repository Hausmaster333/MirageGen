"""Entry point для запуска FastAPI сервера."""

from __future__ import annotations

import uvicorn
from loguru import logger

from avatar.api.app import create_app
from avatar.config import Settings


def run_server() -> None:
    """Запустить FastAPI сервер."""
    settings = Settings()
    app = create_app(settings)
    
    logger.info(
        f"Starting server at {settings.api.host}:{settings.api.port}"
    )
    
    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()