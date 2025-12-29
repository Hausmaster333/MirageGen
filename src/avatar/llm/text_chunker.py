"""Text chunker for streaming LLM → TTS pipeline.

Разбивает поток токенов на чанки для TTS:
- По N словам
- По знакам препинания
- Комбинированный режим
"""

from __future__ import annotations

import re
from typing import AsyncIterator, Literal

from loguru import logger


class TextChunker:
    """Разбивает поток токенов на чанки для TTS.

    Attributes:
        mode: Режим разбиения ("words", "punctuation", "hybrid").
        max_words: Максимум слов в чанке.
        min_words: Минимум слов в чанке.
        buffer: Накопительный буфер токенов.
        total_chunks_yielded: Счетчик выданных чанков (для отладки).
    """

    # Знаки препинания для разбиения
    SENTENCE_TERMINATORS = r'[.!?…]'
    CLAUSE_SEPARATORS = r'[,;:—–]'

    def __init__(
        self,
        mode: Literal["words", "punctuation", "hybrid"] = "hybrid",
        max_words: int = 10,
        min_words: int = 4,
    ) -> None:
        """Инициализация chunker.

        Args:
            mode: Режим разбиения.
            max_words: Максимум слов в чанке.
            min_words: Минимум слов для отправки чанка.
        """
        self.mode = mode
        self.max_words = max_words
        self.min_words = min_words
        self.buffer = ""
        self.total_chunks_yielded = 0
        
        logger.debug(
            f"TextChunker initialized: mode={mode}, max_words={max_words}, "
            f"min_words={min_words}"
        )

    async def process_stream(
        self, token_stream: AsyncIterator[str]
    ) -> AsyncIterator[str]:
        """Обработать поток токенов и выдавать чанки.

        Args:
            token_stream: Async iterator токенов от LLM.

        Yields:
            str: Готовые чанки для TTS.
        """
        logger.debug("Starting stream processing")
        
        async for token in token_stream:
            self.buffer += token
            
            # Логировать рост буфера (опционально, можно отключить)
            # logger.trace(f"Buffer size: {len(self.buffer)} chars, {len(self.buffer.split())} words")

            # Проверить, готов ли чанк
            chunk = self._try_extract_chunk()
            if chunk:
                self.total_chunks_yielded += 1
                logger.debug(
                    f"Yielding chunk #{self.total_chunks_yielded}: "
                    f"{chunk[:50]}... ({len(chunk.split())} words)"
                )
                yield chunk

        # ВАЖНО: Выдать остаток буфера (ВСЕГДА, даже если меньше min_words)
        final_chunk = self.buffer.strip()
        if final_chunk:
            self.total_chunks_yielded += 1
            logger.info(
                f"Yielding FINAL chunk #{self.total_chunks_yielded}: "
                f"{final_chunk[:50]}... ({len(final_chunk.split())} words)"
            )
            yield final_chunk
            self.buffer = ""
        else:
            logger.debug("No final chunk - buffer is empty")
        
        logger.info(f"Stream processing completed. Total chunks: {self.total_chunks_yielded}")

    def _try_extract_chunk(self) -> str | None:
        """Попытаться извлечь чанк из буфера.

        Returns:
            str | None: Чанк или None.
        """
        if self.mode == "words":
            return self._extract_by_words()
        elif self.mode == "punctuation":
            return self._extract_by_punctuation()
        elif self.mode == "hybrid":
            return self._extract_hybrid()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _extract_complete_words(self, text: str, max_pos: int) -> tuple[str, int]:
        """Извлечь только полные слова до позиции max_pos.

        Находит последний пробел ПЕРЕД max_pos и обрезает там.

        Args:
            text: Исходный текст.
            max_pos: Максимальная позиция для обрезки.

        Returns:
            tuple[str, int]: (извлеченный_текст, позиция_конца_в_буфере)
        """
        # Если max_pos за пределами текста, взять весь текст
        if max_pos >= len(text):
            return text.strip(), len(text)

        # Найти последний пробел перед max_pos
        chunk = text[:max_pos]
        
        # Если chunk заканчивается пробелом или знаком препинания - ОК
        if chunk and (chunk[-1].isspace() or chunk[-1] in '.,!?;:—–…'):
            return chunk.strip(), max_pos
        
        # Иначе найти последний пробел
        last_space_idx = chunk.rfind(' ')
        
        if last_space_idx == -1:
            # Нет пробелов - значит одно длинное слово, не извлекаем
            return "", 0
        
        # Обрезать по последнему пробелу
        chunk = text[:last_space_idx].strip()
        return chunk, last_space_idx

    def _extract_by_words(self) -> str | None:
        """Извлечь чанк по количеству слов."""
        words = self.buffer.strip().split()
        
        if len(words) >= self.max_words:
            # Взять ровно max_words слов
            target_text = " ".join(words[:self.max_words])
            
            # Найти эту позицию в буфере
            pos = self.buffer.find(target_text)
            
            if pos != -1:
                end_pos = pos + len(target_text)
                
                # Убедиться что обрезаем по границе слова
                chunk, actual_end = self._extract_complete_words(self.buffer, end_pos)
                
                if chunk and len(chunk.split()) >= self.min_words:
                    self.buffer = self.buffer[actual_end:].lstrip()
                    return chunk
        
        return None

    def _extract_by_punctuation(self) -> str | None:
        """Извлечь чанк до знака препинания."""
        # Ищем конец предложения
        match = re.search(self.SENTENCE_TERMINATORS, self.buffer)
        
        if match:
            end_pos = match.end()
            chunk = self.buffer[:end_pos].strip()
            
            if len(chunk.split()) >= self.min_words:
                self.buffer = self.buffer[end_pos:].lstrip()
                return chunk
        
        # Ищем разделитель (только если достаточно слов накопилось)
        words = self.buffer.strip().split()
        if len(words) >= self.min_words + 2:
            match = re.search(self.CLAUSE_SEPARATORS, self.buffer)
            
            if match:
                end_pos = match.end()
                chunk = self.buffer[:end_pos].strip()
                
                if len(chunk.split()) >= self.min_words:
                    self.buffer = self.buffer[end_pos:].lstrip()
                    return chunk
        
        return None

    def _extract_hybrid(self) -> str | None:
        """Гибридный режим: приоритет пунктуации, fallback на слова."""
        # 1. Попытка по точке/вопросу/восклицанию
        match = re.search(self.SENTENCE_TERMINATORS, self.buffer)
        
        if match:
            end_pos = match.end()
            chunk = self.buffer[:end_pos].strip()
            
            if len(chunk.split()) >= self.min_words:
                self.buffer = self.buffer[end_pos:].lstrip()
                return chunk
        
        # 2. Если буфер большой, проверяем разделители (запятая и т.д.)
        words = self.buffer.strip().split()
        
        if len(words) >= self.max_words - 2:
            # Ищем разделитель в пределах текущего буфера
            match = re.search(self.CLAUSE_SEPARATORS, self.buffer)
            
            if match:
                end_pos = match.end()
                chunk = self.buffer[:end_pos].strip()
                
                if len(chunk.split()) >= self.min_words:
                    self.buffer = self.buffer[end_pos:].lstrip()
                    return chunk
        
        # 3. Если слов накопилось >= max_words, отправляем по словам
        if len(words) >= self.max_words:
            # Найти позицию после max_words-ого слова
            target_words = words[:self.max_words]
            target_text = " ".join(target_words)
            
            # Найти эту позицию в буфере
            pos = 0
            word_count = 0
            
            for i, char in enumerate(self.buffer):
                if char.isspace():
                    continue
                
                # Начало нового слова
                if i == 0 or self.buffer[i-1].isspace():
                    word_count += 1
                    if word_count > self.max_words:
                        pos = i
                        break
            
            if pos > 0:
                # Извлечь полные слова до этой позиции
                chunk, actual_end = self._extract_complete_words(self.buffer, pos)
                
                if chunk and len(chunk.split()) >= self.min_words:
                    self.buffer = self.buffer[actual_end:].lstrip()
                    return chunk
        
        return None

    def reset(self) -> None:
        """Сбросить буфер."""
        self.buffer = ""
        self.total_chunks_yielded = 0
        logger.debug("TextChunker buffer reset")
