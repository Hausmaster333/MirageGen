# === Файл: src/avatar/api/middleware.py ===
"""FastAPI middleware (CORS, logging, error handling)."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов и времени обработки."""

    async def dispatch(self, request: Request, call_next):
        """Обработка запроса с логированием.

        Args:
            request: Входящий HTTP-запрос.
            call_next: Следующий middleware в цепочке.

        Returns:
            Response: HTTP-ответ.
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        return response


def setup_logging_middleware(app: FastAPI) -> None:
    """Настроить logging middleware.

    Args:
        app: FastAPI приложение.
    """
    app.add_middleware(LoggingMiddleware)
    logger.info("Logging middleware configured")
