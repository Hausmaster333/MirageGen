"""Pydantic Settings для всех компонентов (LLM, TTS, Lipsync, Motion, API).

Загрузка из config/models_config.yaml + переменные окружения.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Literal

import yaml
from loguru import logger
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Подавление deprecated warnings от PyTorch (TypedStorage)
warnings.filterwarnings("ignore", category=UserWarning, module="torch.package.package_importer")


class LLMConfig(BaseSettings):
    """Настройки LLM провайдера.

    Attributes:
        provider: Тип провайдера ("ollama", "openai", "anthropic").
        model: Название модели.
        base_url: URL сервера (для Ollama).
        temperature: Температура генерации.
        max_tokens: Максимальное количество токенов.
        system_prompt_ru: Системный промпт для русского языка.
    """

    provider: Literal["ollama", "openai", "anthropic"] = "ollama"
    model: str = "mistral:7b-instruct-q4_K_M"
    base_url: str = "http://localhost:11434"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    system_prompt_ru: str = "Ты — дружелюбный русскоязычный AI-ассистент."


class TTSConfig(BaseSettings):
    """Настройки TTS движка.

    Attributes:
        engine: Тип движка ("xtts", "silero").
        language: Язык синтеза.
        speaker_wav: Путь к WAV для voice cloning (опционально).
        speed: Скорость синтеза.
    """

    engine: Literal["xtts", "silero"] = "silero"
    language: str = "ru"
    speaker_wav: str | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class LipSyncConfig(BaseSettings):
    """Настройки Lip-Sync генератора.

    Attributes:
        generator: Тип генератора ("rhubarb").
        rhubarb_path: Путь к бинарю Rhubarb.
        recognizer: Phonetic recognizer ("pocketSphinx" или "phonetic").
    """

    generator: Literal["rhubarb"] = "rhubarb"
    rhubarb_path: Path = Path("assets/rhubarb/rhubarb")
    recognizer: Literal["pocketSphinx", "phonetic"] = "pocketSphinx"


class MotionConfig(BaseSettings):
    """Настройки Motion генератора.

    Attributes:
        generator: Тип генератора ("preset").
        sentiment_model: Модель для sentiment analysis.
        animations_dir: Директория с preset-анимациями.
        fallback_action: Дефолтное действие при ошибке.
    """

    generator: Literal["preset"] = "preset"
    sentiment_model: str = "blanchefort/rubert-base-cased-sentiment"
    animations_dir: Path = Path("assets/animations")
    fallback_action: str = "idle"


class APIConfig(BaseSettings):
    """Настройки FastAPI сервера.

    Attributes:
        host: Хост сервера.
        port: Порт сервера.
        cors_origins: Список CORS origins.
    """

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class Settings(BaseSettings):
    """Главные настройки приложения.

    Attributes:
        llm: Настройки LLM.
        tts: Настройки TTS.
        lipsync: Настройки Lip-Sync.
        motion: Настройки Motion.
        api: Настройки API.
    """

    model_config = SettingsConfigDict(
        env_prefix="AVATAR_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    llm: LLMConfig = Field(default_factory=LLMConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    lipsync: LipSyncConfig = Field(default_factory=LipSyncConfig)
    motion: MotionConfig = Field(default_factory=MotionConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    @classmethod
    def load_from_yaml(cls, yaml_path: Path) -> Settings:
        """Загрузить настройки из YAML-файла.

        Args:
            yaml_path: Путь к YAML-файлу.

        Returns:
            Settings: Загруженные настройки.

        Raises:
            FileNotFoundError: Если файл не существует.
            ValueError: Если YAML невалиден.
        """
        yaml_path = Path(yaml_path)

        # Проверка существования файла
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {yaml_path}")

        logger.debug(f"Loading settings from YAML: {yaml_path}")

        try:
            # Чтение YAML
            with Path(yaml_path).open(encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)

            if not config_dict:
                raise ValueError(f"Empty YAML config: {yaml_path}")

            # Создание Settings из dict
            settings = cls(**config_dict)
            logger.info(f"Settings loaded from {yaml_path}")
            return settings

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML syntax in {yaml_path}: {e}")
            raise ValueError(f"Invalid YAML config: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load settings from {yaml_path}: {e}")
            raise ValueError(f"Failed to load settings: {e}") from e
