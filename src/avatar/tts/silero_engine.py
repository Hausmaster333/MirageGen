# === Файл: src/avatar/tts/silero_engine.py ===
"""Silero TTS Engine implementation (легковесный fallback для русского).

Нативная поддержка русского языка, быстрая генерация, малый VRAM-footprint.
"""
from pathlib import Path  # В начало файла
import soundfile
import torch
import torchaudio
import io
from typing import AsyncIterator
from loguru import logger
from avatar.interfaces.tts import ITTSEngine
from avatar.schemas.audio_types import AudioSegment


class SileroEngine(ITTSEngine):
    def __init__(
            self,
            language: str = "ru",
            speaker: str = "xenia",
            sample_rate: int = 48000,
            device: str = "cpu"
    ) -> None:



        if language != "ru":
            raise ValueError("SileroEngine supports only 'ru'")



        self.language = language
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.device = torch.device(device)
        self._model = None

        logger.info(f"SileroEngine initialized: speaker={speaker}, sample_rate={sample_rate}, device={device}")

    def _load_model(self):
        if self._model is None:
            model_path = Path("assets/silero/model.pt")

            # Если модели нет локально - скачиваем
            if not model_path.exists():
                logger.info("Downloading Silero V5 model manually (via requests)...")
                model_path.parent.mkdir(parents=True, exist_ok=True)

                url = "https://models.silero.ai/models/tts/ru/v5_ru.pt"

                try:
                    import requests
                    from tqdm import tqdm

                    # Открываем соединение в потоковом режиме
                    response = requests.get(url, stream=True, timeout=100)
                    response.raise_for_status()  # Проверка на ошибки (404, 500)

                    total_size = int(response.headers.get('content-length', 0))
                    block_size = 1024  # 1 KB

                    with open(model_path, "wb") as file, tqdm(
                            desc="Silero Model",
                            total=total_size,
                            unit="iB",
                            unit_scale=True,
                            unit_divisor=1024,
                    ) as bar:
                        for data in response.iter_content(block_size):
                            size = file.write(data)
                            bar.update(size)

                    logger.info(f"Model downloaded to {model_path}")

                except Exception as e:
                    # Если скачивание упало - удаляем недокачанный файл
                    if model_path.exists():
                        model_path.unlink()
                    logger.error(f"Failed to download model: {e}")
                    raise RuntimeError(
                        f"Could not download Silero model. Please download manually from {url} to {model_path}") from e

            else:
                logger.info(f"Using local model from {model_path}")

            # Загружаем локальный файл
            try:
                self._model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
                self._model.to(self.device)
            except Exception as e:
                logger.error(f"Failed to load model from disk: {e}")
                raise RuntimeError("Model file is corrupted. Delete assets/silero/model.pt and try again.") from e

        return self._model

    async def synthesize(
            self,
            text: str,
            language: str = "ru",
            speaker_wav: str | None = None
    ) -> AudioSegment:
        if not text:
            raise ValueError("Text is empty")

        model = self._load_model()

        # Генерация аудио (тензор)
        audio_tensor = model.apply_tts(
            text=text,
            speaker=self.speaker,
            sample_rate=self.sample_rate
        )

        # Конвертация тензора в байты (WAV)
        buffer = io.BytesIO()
        import soundfile as sf

        # audio_tensor имеет форму [Time] или [1, Time]. soundfile хочет [Time] (numpy)
        audio_numpy = audio_tensor.detach().cpu().numpy()
        if len(audio_numpy.shape) > 1:
            audio_numpy = audio_numpy.squeeze()

        sf.write(buffer, audio_numpy, self.sample_rate, format='WAV', subtype='PCM_16')

        audio_bytes = buffer.getvalue()

        duration = len(audio_tensor) / self.sample_rate

        return AudioSegment(
            audio_bytes=audio_bytes,
            sample_rate=self.sample_rate,
            format="wav",
            duration=duration
        )

    async def synthesize_streaming(
            self,
            text: str,
            language: str = "ru"
    ) -> AsyncIterator[AudioSegment]:
        # Простое разбиение по знакам препинания для PoC
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)

        for sentence in sentences:
            if not sentence.strip():
                continue
            yield await self.synthesize(sentence)


    def get_supported_languages(self) -> list[str]:
        """Список поддерживаемых языков.

        Returns:
            list[str]: Только ["ru"].
        """
        return ["ru"]
