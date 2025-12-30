# === Файл: src/avatar/pipeline/avatar_pipeline.py ===
"""Avatar Pipeline Orchestrator (главный координатор компонентов).

Объединяет LLM → TTS → Lipsync → Motion в единый streaming-пайплайн.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from avatar.interfaces.pipeline import IPipeline
from avatar.llm.text_chunker import TextChunker
from avatar.motion.sentiment_analyzer import SentimentAnalyzer
from avatar.schemas.api_types import AvatarFrame
from avatar.schemas.llm_types import Message
from avatar.tts.audio_utils import save_audio_segment

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from avatar.interfaces.lipsync import ILipSyncGenerator
    from avatar.interfaces.llm import ILLMProvider
    from avatar.interfaces.motion import IMotionGenerator
    from avatar.interfaces.tts import ITTSEngine
    from avatar.schemas.audio_types import AudioSegment


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
        messages = list(conversation_history or [])
        messages.append(Message(role="user", content=user_input))

        # Таймлайн для фреймов (монотонно растёт)
        timeline_ts = 0.0

        # Обработать через LLM → TTS → Lipsync → Motion
        async for text_chunk in self._process_llm_stream(messages):
            try:
                # 1. TTS → получаем AudioSegment
                audio_segment = await self.tts_engine.synthesize(text_chunk)
                audio_bytes = audio_segment.audio_bytes
                duration = audio_segment.duration

                # 2. Lipsync → используем AudioSegment напрямую
                blendshapes_dict = await self._process_lipsync(audio_segment)

                # 3. Sentiment → Motion
                emotion = await self._detect_emotion(text_chunk)
                motion_dict = await self._process_motion(emotion=emotion, duration=duration)

                # 4. Собираем AvatarFrame
                frame = AvatarFrame(  # pyright: ignore[reportCallIssue]
                    timestamp=timeline_ts,
                    text_chunk=text_chunk,
                    audio_chunk=audio_bytes,
                    blendshapes=blendshapes_dict or None,
                    motion=motion_dict or None,
                )
                yield frame

                # Сдвигаем таймлайн
                timeline_ts += duration

            except Exception as e:
                logger.exception(f"Failed to process chunk: {e}")
                raise RuntimeError(f"Pipeline error: {e}") from e

    async def healthcheck(self) -> dict[str, bool]:
        """Healthcheck всех компонентов пайплайна.

        Returns:
            dict[str, bool]: Статус компонентов {"llm": True, "tts": True, ...}.
        """

        async def _check(component: object, name: str) -> bool:
            try:
                method = getattr(component, "healthcheck", None) or getattr(component, "health_check", None)
                if method is None:
                    logger.debug(f"Component {name} has no healthcheck method, assuming healthy")
                    return True

                result = method()
                # Если метод async
                if hasattr(result, "__await__"):
                    result = await result
                return bool(result)
            except Exception:
                logger.exception(f"Healthcheck failed for {name}")
                return False

        return {
            "llm": await _check(self.llm_provider, "llm"),
            "tts": await _check(self.tts_engine, "tts"),
            "lipsync": await _check(self.lipsync_generator, "lipsync"),
            "motion": await _check(self.motion_generator, "motion"),
        }

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
                logger.debug(f"Yielding text chunk #{chunk_count}: {chunk[:50]}... ({len(chunk)} chars)")
                yield chunk

            logger.info(f"LLM stream completed: {chunk_count} chunks generated")

        except Exception as e:
            logger.exception(f"LLM stream processing failed: {e}")
            raise RuntimeError(f"LLM stream error: {e}") from e

    async def _process_lipsync(self, audio_segment: AudioSegment) -> dict[str, float]:
        """Генерация blendshapes для аудио.

        Args:
            audio_segment: AudioSegment с байтами WAV.

        Returns:
            dict[str, float]: Blendshape weights для текущего фрейма (например, {"viseme_aa": 0.8}).
        """
        logger.debug(f"Generating lipsync for audio: {audio_segment.duration:.2f}s")

        temp_path: Path | None = None
        try:
            # 1. Создаем временный WAV файл
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            # Сохраняем наши байты во временный файл
            save_audio_segment(audio_segment, temp_path)
            logger.debug(f"Temporary audio saved to: {temp_path}")

            # 2. Вызываем lipsync генератор (возвращает BlendshapeWeights)
            blendshape_weights = await self.lipsync_generator.generate_blendshapes(temp_path)  # pyright: ignore[reportAttributeAccessIssue]

            # 3. Конвертируем BlendshapeWeights → dict[str, float] для AvatarFrame
            # Берём средние веса по всем кадрам (или первый кадр)
            if not blendshape_weights.frames:
                logger.warning("Lipsync returned empty frames")
                return {}

            # Вариант 1: берём первый кадр
            first_frame = blendshape_weights.frames[0]
            mouth_shapes = first_frame.mouth_shapes  # dict[str, float]

            # Mapping Rhubarb phonemes → Three.js visemes (как в SPEC.md)
            phoneme_map = self.lipsync_generator.get_phoneme_mapping()
            result = {}
            for phoneme, weight in mouth_shapes.items():
                viseme = phoneme_map.get(phoneme, phoneme)  # fallback к оригинальному
                result[viseme] = weight

            logger.debug(f"Lipsync generated: {len(result)} blendshapes")
            return result

        except Exception as e:
            logger.exception(f"Lipsync processing failed: {e}")
            # Возвращаем пустые blendshapes при ошибке
            return {}

        finally:
            # 4. ОБЯЗАТЕЛЬНО удаляем временный файл
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                    logger.debug("Temporary audio file cleaned up")
                except Exception:
                    logger.warning("Failed to cleanup temp audio", exc_info=True)

    async def _detect_emotion(self, text: str) -> str:
        """Определить эмоцию из текста через SentimentAnalyzer.

        Args:
            text: Текст для анализа.

        Returns:
            str: Эмоция ("happy", "sad", "neutral", "thinking").
        """
        try:
            # SentimentAnalyzer может иметь разные методы
            for method_name in ("analyze", "predict", "predict_emotion", "__call__"):
                method = getattr(self.sentiment_analyzer, method_name, None)
                if method is None:
                    continue

                result = method(text)
                # Если async
                if hasattr(result, "__await__"):
                    result = await result

                # Извлекаем строку эмоции
                if isinstance(result, str):
                    return result.strip().lower()

                # Если вернулся объект с полем label/emotion
                for attr in ("label", "emotion"):
                    val = getattr(result, attr, None)
                    if isinstance(val, str) and val.strip():
                        return val.strip().lower()

            # Fallback
            logger.debug("Sentiment analyzer returned no valid emotion, using neutral")
            return "neutral"

        except Exception:
            logger.exception("Sentiment analysis failed, fallback to neutral")
            return "neutral"

    async def _process_motion(self, emotion: str, duration: float) -> dict[str, tuple[float, float, float, float]]:
        """Генерация motion для эмоции.

        Args:
            emotion: Эмоция (happy/sad/neutral/thinking).
            duration: Длительность анимации.

        Returns:
            dict[str, tuple[float, float, float, float]]: Bone rotations (quaternions).
        """
        try:
            # Вызываем IMotionGenerator.generate_motion() → возвращает MotionKeyframes
            motion_keyframes = await self.motion_generator.generate_motion(
                emotion=emotion,
                duration=duration,
            )

            # Конвертируем MotionKeyframes → dict для AvatarFrame
            # Берём первый keyframe (или средний)
            if not motion_keyframes.keyframes:
                logger.debug("Motion returned empty keyframes")
                return {}

            first_keyframe = motion_keyframes.keyframes[0]
            bone_rotations = first_keyframe.bone_rotations  # dict[str, tuple[float, float, float, float]]

            logger.debug(f"Motion generated: {len(bone_rotations)} bones")
            return bone_rotations

        except Exception:
            logger.exception("Motion generation failed, returning empty motion")
            return {}
