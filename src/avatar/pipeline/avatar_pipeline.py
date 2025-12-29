# === Файл: src/avatar/pipeline/avatar_pipeline.py ===
"""Avatar Pipeline Orchestrator (главный координатор компонентов).

Объединяет LLM → TTS → Lipsync → Motion в единый streaming-пайплайн.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator

from loguru import logger

from avatar.interfaces.lipsync import ILipSyncGenerator
from avatar.interfaces.llm import ILLMProvider
from avatar.interfaces.motion import IMotionGenerator
from avatar.interfaces.pipeline import IPipeline
from avatar.interfaces.tts import ITTSEngine
from avatar.motion.sentiment_analyzer import SentimentAnalyzer
from avatar.schemas.api_types import AvatarFrame
from avatar.schemas.llm_types import Message
from avatar.llm.text_chunker import TextChunker

if TYPE_CHECKING:
    pass


class AvatarPipeline(IPipeline):
    """Avatar Pipeline Orchestrator.

    Attributes:
        llm_provider: LLM провайдер.
        tts_engine: TTS движок.
        lipsync_generator: Lip-sync генератор.
        motion_generator: Motion генератор.
        sentiment_analyzer: Sentiment analyzer для определения эмоции.
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        tts_engine: ITTSEngine,
        lipsync_generator: ILipSyncGenerator,
        motion_generator: IMotionGenerator,
        sentiment_analyzer: SentimentAnalyzer | None = None,
    ) -> None:
        """Инициализация AvatarPipeline.

        Args:
            llm_provider: LLM провайдер.
            tts_engine: TTS движок.
            lipsync_generator: Lip-sync генератор.
            motion_generator: Motion генератор.
            sentiment_analyzer: Опциональный sentiment analyzer.
        """
        self.llm_provider = llm_provider
        self.tts_engine = tts_engine
        self.lipsync_generator = lipsync_generator
        self.motion_generator = motion_generator
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        logger.info("AvatarPipeline initialized with all components")

    async def process(
        self,
        user_input: str,
        conversation_history: list[Message] | None = None,
    ) -> AsyncIterator[AvatarFrame]:
        """Обработка пользовательского ввода → стриминг AvatarFrame.

        Args:
            user_input: Текст запроса пользователя.
            conversation_history: Опциональная история диалога.

        Yields:
            AvatarFrame: Кадры с текстом/аудио/blendshapes/motion.

        Raises:
            ValueError: Если user_input пустой или слишком длинный.
            RuntimeError: Если любой компонент упал.
        """
        # Валидация
        if not user_input or not user_input.strip():
            raise ValueError("user_input cannot be empty")
        
        if len(user_input) > 2000:
            raise ValueError(f"user_input too long: {len(user_input)} chars (max 2000)")
        
        logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Подготовить messages
        messages = conversation_history or []
        messages.append(Message(role="user", content=user_input))
        
        # Обработать через LLM → TTS → Lipsync → Motion
        async for text_chunk in self._process_llm_stream(messages):
            try:
                # 1. Синтезировать аудио
                audio_bytes, duration = await self._process_tts_chunk(text_chunk)
                
                # 2. Генерировать blendshapes (stub - реализуете позже)
                # blendshapes = await self._process_lipsync(audio_path)
                
                # 3. Генерировать motion (stub - реализуете позже)
                # Сначала через sentiment_analyze получаем emotion, а duration выше получаем
                # motion = await self._process_motion(emotion, duration)
                
                # 4. Создать AvatarFrame
                frame = AvatarFrame(
                    text=text_chunk,
                    audio=audio_bytes,
                    # blendshapes=blendshapes,  # TODO
                    # motion=motion,  # TODO
                )
                
                yield frame
                
            except Exception as e:
                logger.error(f"Failed to process chunk: {e}")
                # Можно пропустить проблемный чанк или прервать
                raise RuntimeError(f"Pipeline error: {e}") from e

    async def healthcheck(self) -> dict[str, bool]:
        """Healthcheck всех компонентов пайплайна.

        Returns:
            dict[str, bool]: Статус компонентов {"llm": True, "tts": True, ...}.
        """
        raise NotImplementedError("TODO: Implement healthcheck")

    async def _process_llm_stream(
        self,
        messages: list[Message],
    ) -> AsyncIterator[str]:
        """Стриминг LLM-генерации с разбиением на чанки для TTS.

        Args:
            messages: История диалога.

        Yields:
            str: Текстовые чанки (готовые для TTS).
        """
        logger.debug(f"Starting LLM stream processing for {len(messages)} messages")
        
        # Создать chunker
        chunker = TextChunker(mode="hybrid", max_words=10, min_words=4)
        
        try:
            # Получить stream от LLM
            llm_stream = self.llm_provider.generate_stream(
                messages=messages,
                temperature=0.7,
                max_tokens=512,
            )
            
            # Обработать через chunker и выдавать чанки
            chunk_count = 0
            async for chunk in chunker.process_stream(llm_stream):
                chunk_count += 1
                logger.debug(
                    f"Yielding text chunk #{chunk_count}: "
                    f"{chunk[:50]}... ({len(chunk)} chars)"
                )
                yield chunk
            
            logger.info(f"LLM stream completed: {chunk_count} chunks generated")
            
        except Exception as e:
            logger.error(f"LLM stream processing failed: {e}")
            raise RuntimeError(f"LLM stream error: {e}") from e

    async def _process_tts_chunk(self, text_chunk: str) -> bytes:
        """Генерация TTS для текстового чанка.

        Args:
            text_chunk: Текст для озвучки.

        Returns:
            bytes: Аудио-байты.
        """
        logger.debug(f"Synthesizing TTS for chunk: {text_chunk[:50]}...")
        
        try:
            # Синтезировать аудио
            audio_segment = await self.tts_engine.synthesize(
                text=text_chunk,
                language="ru",
            )
            
            logger.debug(
                f"TTS synthesis completed: {audio_segment.duration:.2f}s, "
                f"{len(audio_segment.audio_bytes)} bytes"
            )
            
            return audio_segment.audio_bytes, audio_segment.duration
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise RuntimeError(f"TTS error: {e}") from e

    async def _process_lipsync(self, audio_path: Path) -> dict[str, float]:
        """Генерация blendshapes для аудио.

        Args:
            audio_path: Путь к аудио-файлу.

        Returns:
            dict[str, float]: Blendshape weights.
        """
        raise NotImplementedError("TODO: Implement _process_lipsync")

    async def _process_motion(self, emotion: str, duration: float) -> dict:
        """Генерация motion для эмоции.

        Args:
            emotion: Эмоция.
            duration: Длительность анимации.

        Returns:
            dict: Motion keyframe data.
        """
        raise NotImplementedError("TODO: Implement _process_motion")
