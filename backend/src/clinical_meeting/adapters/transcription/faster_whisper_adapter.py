"""faster-whisper transcription adapter (Hugging Face Systran models)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from clinical_meeting.constants import (
    DEFAULT_WHISPER_COMPUTE_TYPE,
    DEFAULT_WHISPER_DEVICE,
    DEFAULT_WHISPER_MODEL_SIZE,
)
from clinical_meeting.domain.models import TranscriptSegment


class FasterWhisperAdapter:
    """Lazy-loads WhisperModel; maps segments to domain TranscriptSegment."""

    def __init__(
        self,
        model_size: str = DEFAULT_WHISPER_MODEL_SIZE,
        device: str = DEFAULT_WHISPER_DEVICE,
        compute_type: str = DEFAULT_WHISPER_COMPUTE_TYPE,
    ) -> None:
        self._model_size = model_size
        self._device_setting = device
        self._compute_type_setting = compute_type
        self._model: Any | None = None

    @property
    def model_name(self) -> str:
        return f"faster-whisper-{self._model_size}"

    def _resolve_device(self) -> str:
        if self._device_setting != "auto":
            return self._device_setting
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _resolve_compute_type(self, device: str) -> str:
        if self._compute_type_setting != "default":
            return self._compute_type_setting
        return "float16" if device == "cuda" else "int8"

    def _ensure_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError(
                "faster-whisper is not installed. Install backend deps including faster-whisper."
            ) from exc
        device = self._resolve_device()
        compute_type = self._resolve_compute_type(device)
        self._model = WhisperModel(
            self._model_size,
            device=device,
            compute_type=compute_type,
        )
        return self._model

    def transcribe(self, audio_path: Path) -> list[TranscriptSegment]:
        model = self._ensure_model()
        segments_iter, _info = model.transcribe(str(audio_path), beam_size=5)
        result: list[TranscriptSegment] = []
        for segment in segments_iter:
            text = (segment.text or "").strip()
            if not text:
                continue
            result.append(
                TranscriptSegment(
                    start_seconds=float(segment.start),
                    end_seconds=float(segment.end),
                    text=text,
                )
            )
        return result
