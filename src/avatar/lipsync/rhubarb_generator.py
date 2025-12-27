# === Файл: src/avatar/lipsync/rhubarb_generator.py ===
"""Rhubarb Lip-Sync Generator implementation.

CLI-обёртка для Rhubarb Lip-Sync (https://github.com/DanielSWolf/rhubarb-lip-sync).
Генерирует phoneme-based blendshape анимацию из аудио.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from avatar.interfaces.lipsync import ILipSyncGenerator
from avatar.schemas.animation_types import BlendshapeFrame, BlendshapeWeights

if TYPE_CHECKING:
    pass


class RhubarbGenerator(ILipSyncGenerator):
    """Rhubarb Lip-Sync Generator (CLI wrapper).

    Attributes:
        rhubarb_path: Путь к бинарю Rhubarb.
        recognizer: Phonetic recognizer ("pocketSphinx" или "phonetic").
        phoneme_mapping: Mapping Rhubarb phonemes → Three.js blendshapes.
    """

    def __init__(
        self,
        rhubarb_path: Path = Path("assets/rhubarb/rhubarb"),
        recognizer: str = "pocketSphinx",
    ) -> None:
        """Инициализация RhubarbGenerator.

        Args:
            rhubarb_path: Путь к бинарю Rhubarb.
            recognizer: Phonetic recognizer.

        Raises:
            FileNotFoundError: Если бинарь Rhubarb не найден.
        """
        if not rhubarb_path.exists():
            msg = f"Rhubarb binary not found: {rhubarb_path}"
            raise FileNotFoundError(msg)
        self.rhubarb_path = rhubarb_path
        self.recognizer = recognizer
        self._phoneme_mapping = self._build_phoneme_mapping()
        logger.info(f"RhubarbGenerator initialized: rhubarb_path={rhubarb_path}")

    def _build_phoneme_mapping(self) -> dict[str, str]:
        """Создать mapping Rhubarb phonemes → Three.js blendshapes.

        Returns:
            dict[str, str]: Mapping (например, {"A": "viseme_aa", "B": "viseme_PP"}).
        """
        return {
            "A": "viseme_aa",
            "B": "viseme_PP",
            "C": "viseme_E",
            "D": "viseme_aa",  # tongue down variant
            "E": "viseme_O",
            "F": "viseme_FF",
            "G": "viseme_TH",
            "H": "viseme_DD",
            "X": "viseme_sil",  # rest/silence
        }

    async def generate_blendshapes(
        self,
        audio_path: Path,
        recognizer: str = "pocketSphinx",
    ) -> BlendshapeWeights:
        """Генерация blendshape-кадров из аудио через Rhubarb CLI.

        Args:
            audio_path: Путь к аудио-файлу (WAV).
            recognizer: Phonetic recognizer.

        Returns:
            BlendshapeWeights: Набор кадров blendshape.

        Raises:
            FileNotFoundError: Если audio_path не существует.
            RuntimeError: Если Rhubarb завершился с ошибкой.
        """
        if not audio_path.exists():
            msg = f"Audio file not found: {audio_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Generating blendshapes for audio: {audio_path}")
        
        rhubarb_json = self._run_rhubarb(audio_path, recognizer)
        blendshape_weights = self._parse_rhubarb_output(rhubarb_json)
        
        logger.info(
            f"Generated {len(blendshape_weights.frames)} blendshape frames "
            f"(duration: {blendshape_weights.duration:.2f}s)"
        )
        
        return blendshape_weights

    def get_phoneme_mapping(self) -> dict[str, str]:
        """Mapping Rhubarb phonemes → Three.js blendshapes.

        Returns:
            dict[str, str]: Phoneme mapping.
        """
        return self._phoneme_mapping

    def _run_rhubarb(self, audio_path: Path, recognizer: str) -> dict:
        """Запустить Rhubarb CLI и распарсить JSON-вывод.

        Args:
            audio_path: Путь к аудио-файлу.
            recognizer: Recognizer ("pocketSphinx" или "phonetic").

        Returns:
            dict: Rhubarb JSON output (mouthCues, metadata).

        Raises:
            RuntimeError: Если Rhubarb упал с ошибкой.
        """
        cmd = [
            str(self.rhubarb_path),
            "-f", "json",
            "-r", recognizer,
            str(audio_path),
        ]
        
        logger.debug(f"Running Rhubarb CLI: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            )
            
            rhubarb_json = json.loads(result.stdout)
            logger.debug(f"Rhubarb output parsed successfully")
            return rhubarb_json
            
        except subprocess.CalledProcessError as e:
            msg = f"Rhubarb CLI failed with code {e.returncode}: {e.stderr}"
            logger.error(msg)
            raise RuntimeError(msg) from e
        except subprocess.TimeoutExpired as e:
            msg = f"Rhubarb CLI timed out after 300s"
            logger.error(msg)
            raise RuntimeError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Failed to parse Rhubarb JSON output: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def _parse_rhubarb_output(self, rhubarb_json: dict) -> BlendshapeWeights:
        """Парсинг JSON-вывода Rhubarb в BlendshapeWeights.

        Args:
            rhubarb_json: JSON-вывод Rhubarb (mouthCues).

        Returns:
            BlendshapeWeights: Blendshape frames.
        """
        mouth_cues = rhubarb_json.get("mouthCues", [])
        metadata = rhubarb_json.get("metadata", {})
        duration = metadata.get("duration", 0.0)
        
        if not mouth_cues:
            logger.warning("No mouth cues found in Rhubarb output")
            return BlendshapeWeights(frames=[], fps=30, duration=duration)
        
        frames = []
        for cue in mouth_cues:
            timestamp = cue.get("start", 0.0)
            phoneme = cue.get("value", "X")
            
            blendshape_name = self._phoneme_mapping.get(phoneme, "viseme_sil")
            
            frame = BlendshapeFrame(
                timestamp=timestamp,
                mouth_shapes={blendshape_name: 1.0}
            )
            frames.append(frame)
        
        logger.debug(f"Parsed {len(frames)} frames from Rhubarb output")
        
        return BlendshapeWeights(
            frames=frames,
            fps=30,
            duration=duration
        )
