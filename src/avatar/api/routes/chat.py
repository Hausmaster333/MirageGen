# === Файл: src/avatar/api/routes/chat.py (обновлённый) ===
"""POST /api/v1/chat endpoint (non-streaming)."""

from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from avatar.api.dependencies import get_pipeline
from avatar.schemas.animation_types import BlendshapeFrame, BlendshapeWeights, MotionKeyframe, MotionKeyframes
from avatar.schemas.api_types import AudioSegmentResponse, ChatRequest, ChatResponse

if TYPE_CHECKING:
    from avatar.pipeline.avatar_pipeline import AvatarPipeline

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    pipeline: AvatarPipeline = Depends(get_pipeline),  # noqa: B008
) -> ChatResponse:
    """POST /api/v1/chat - генерация аватар-ответа (non-streaming)."""

    start_time = time.time()

    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")

        full_text_chunks: list[str] = []
        all_audio_bytes: list[bytes] = []
        all_blendshapes: list[dict] = []
        all_motion: list[dict] = []

        async for frame in pipeline.process(
            user_input=request.message,
            conversation_history=request.conversation_history,
        ):
            if frame.text_chunk:
                full_text_chunks.append(frame.text_chunk)
            if frame.audio_chunk:
                all_audio_bytes.append(frame.audio_chunk)
            if frame.blendshapes:
                all_blendshapes.append({"timestamp": frame.timestamp, "weights": frame.blendshapes})
            if frame.motion:
                all_motion.append({"timestamp": frame.timestamp, "rotations": frame.motion})

        full_text = " ".join(full_text_chunks)
        merged_audio = b"".join(all_audio_bytes)

        # Кодируем аудио в base64 для JSON
        audio_response = AudioSegmentResponse(
            audio_bytes_base64=base64.b64encode(merged_audio).decode("utf-8"),
            sample_rate=48000,
            format="wav",
            duration=len(all_audio_bytes) * 1.0,
        )

        blendshape_frames = [
            BlendshapeFrame(timestamp=bs["timestamp"], mouth_shapes=bs["weights"]) for bs in all_blendshapes
        ]
        blendshapes = BlendshapeWeights(
            frames=blendshape_frames,
            fps=30,
            duration=len(blendshape_frames) / 30.0 if blendshape_frames else 0.0,
        )

        motion_keyframes_list = [
            MotionKeyframe(
                timestamp=m["timestamp"],
                bone_rotations=m["rotations"],
                bone_positions={},
            )
            for m in all_motion
        ]
        motion = MotionKeyframes(
            keyframes=motion_keyframes_list,
            emotion="neutral",
            duration=len(motion_keyframes_list) * 1.0 if motion_keyframes_list else 0.0,
        )

        processing_time = time.time() - start_time

        return ChatResponse(
            full_text=full_text,
            audio=audio_response,
            blendshapes=blendshapes,
            motion=motion,
            processing_time=processing_time,
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.exception(f"Chat endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during chat processing",
        ) from e
