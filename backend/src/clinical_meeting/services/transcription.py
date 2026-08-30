"""Validate audio, transcribe via provider, format for ingest."""

from __future__ import annotations

import tempfile
from pathlib import Path

from clinical_meeting.constants import (
    ALLOWED_AUDIO_SUFFIXES,
    DEFAULT_MAX_AUDIO_UPLOAD_BYTES,
    DEFAULT_TRANSCRIPT_SPEAKER,
)
from clinical_meeting.ports import TranscriptionProvider
from clinical_meeting.services.transcript_formatter import segments_to_transcript


class TranscriptionService:
    def __init__(
        self,
        provider: TranscriptionProvider,
        max_audio_bytes: int = DEFAULT_MAX_AUDIO_UPLOAD_BYTES,
        default_speaker: str = DEFAULT_TRANSCRIPT_SPEAKER,
    ) -> None:
        self._provider = provider
        self._max_audio_bytes = max_audio_bytes
        self._default_speaker = default_speaker

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    def validate_audio(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> None:
        del content_type  # suffix is the primary gate; MIME varies by browser
        if len(content) == 0:
            raise ValueError("Audio file is empty")
        if len(content) > self._max_audio_bytes:
            raise ValueError(f"Audio exceeds max size of {self._max_audio_bytes} bytes")
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_AUDIO_SUFFIXES:
            allowed = ", ".join(sorted(ALLOWED_AUDIO_SUFFIXES))
            raise ValueError(f"Unsupported audio type. Allowed: {allowed}")

    def transcribe_to_text(
        self,
        filename: str,
        content: bytes,
        default_speaker: str | None = None,
        content_type: str | None = None,
    ) -> str:
        self.validate_audio(filename, content, content_type)
        speaker = (default_speaker or self._default_speaker).strip() or self._default_speaker
        suffix = Path(filename).suffix.lower() or ".wav"
        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            try:
                segments = self._provider.transcribe(tmp_path)
            except Exception as exc:
                raise RuntimeError(f"Transcription failed: {exc}") from exc
        finally:
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

        if not segments:
            raise ValueError("No speech detected in audio")
        return segments_to_transcript(segments, speaker)
