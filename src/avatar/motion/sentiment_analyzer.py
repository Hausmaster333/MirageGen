# === Файл: src/avatar/motion/sentiment_analyzer.py ===
"""Sentiment Analyzer (RuBERT для русского языка).

Используется для определения эмоции из текста (happy/sad/neutral).
"""

from __future__ import annotations

from typing import Literal

from loguru import logger
from transformers import pipeline


class SentimentAnalyzer:
    """Sentiment Analyzer на основе RuBERT.

    Attributes:
        model_name: Название модели HuggingFace.
        pipeline: Transformers pipeline для sentiment analysis.
        emotion_mapping: Mapping sentiment labels → emotion.
    """

    def __init__(
        self,
        model_name: str = "blanchefort/rubert-base-cased-sentiment",
    ) -> None:
        """Инициализация SentimentAnalyzer.

        Args:
            model_name: Название модели HuggingFace.
        """
        self.model_name = model_name
        self._pipeline: pipeline | None = None  # pyright: ignore[reportGeneralTypeIssues]
        self._emotion_mapping = self._build_emotion_mapping()
        logger.info(f"SentimentAnalyzer initialized: model={model_name}")

    def _build_emotion_mapping(self) -> dict[str, Literal["happy", "sad", "neutral"]]:
        """Создать mapping RuBERT labels → emotion.

        Returns:
            dict: Mapping (например, {"POSITIVE": "happy", "NEGATIVE": "sad", ...}).
        """
        return {
            "POSITIVE": "happy",
            "NEGATIVE": "sad",
            "NEUTRAL": "neutral",
        }

    def _load_pipeline(self) -> pipeline:  # pyright: ignore[reportGeneralTypeIssues]
        """Lazy-loading Transformers pipeline.

        Returns:
            pipeline: Sentiment analysis pipeline.

        Raises:
            RuntimeError: Если загрузка модели не удалась.
        """
        if self._pipeline is not None:
            return self._pipeline

        try:
            logger.info(f"Loading sentiment model: {self.model_name}")

            self._pipeline = pipeline(  # pyright: ignore[reportCallIssue]
                "sentiment-analysis",  # pyright: ignore[reportArgumentType]
                model=self.model_name,
                device=-1,  # CPU by default
            )
            logger.info(f"Model loaded successfully: {self.model_name}")
            return self._pipeline

        except ImportError as e:
            msg = "transformers library not installed. Install with: pip install transformers torch"
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"Failed to load sentiment model {self.model_name}: {e}"
            raise RuntimeError(msg) from e

    async def analyze(self, text: str) -> Literal["happy", "sad", "neutral", "thinking"]:
        """Анализ эмоции из текста.

        Args:
            text: Текст для анализа.

        Returns:
            Literal: Эмоция ("happy", "sad", "neutral", "thinking").

        Raises:
            ValueError: Если текст пустой.
            RuntimeError: Если модель не загружена или ошибка inference.
        """
        # Валидация входных данных
        if not text or not text.strip():
            msg = "Text cannot be empty"
            raise ValueError(msg)

        text = text.strip()
        logger.debug(f"Analyzing sentiment for text: {text[:50]}...")

        try:
            # Загрузка pipeline если необходимо
            pipe = self._load_pipeline()

            # Inference
            result = pipe(text, truncation=True, max_length=512)

            if not result or not isinstance(result, list) or len(result) == 0:
                logger.warning("Empty result from sentiment model, defaulting to neutral")
                return "neutral"

            # Извлечение label и score
            prediction = result[0]
            label = prediction.get("label", "NEUTRAL")
            score = prediction.get("score", 0.0)

            logger.debug(f"Sentiment result: label={label}, score={score:.3f}")

            # Маппинг на эмоцию
            emotion = self._map_label_to_emotion(label)

            # Определение "thinking" на основе низкой уверенности
            if score < 0.6:
                logger.debug(f"Low confidence score {score:.3f}, returning 'thinking'")
                return "thinking"

            logger.info(f"Sentiment analysis complete: emotion={emotion}")
            return emotion

        except Exception as e:
            msg = f"Sentiment analysis failed: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def _map_label_to_emotion(
        self,
        label: str,
    ) -> Literal["happy", "sad", "neutral", "thinking"]:
        """Маппинг RuBERT label → emotion.

        Args:
            label: Label из RuBERT ("POSITIVE", "NEGATIVE", "NEUTRAL").

        Returns:
            Literal: Эмоция.
        """
        return self._emotion_mapping.get(label.upper(), "neutral")
