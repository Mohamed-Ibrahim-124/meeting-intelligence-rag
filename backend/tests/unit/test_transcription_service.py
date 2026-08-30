import pytest

from clinical_meeting.domain.models import TranscriptSegment
from clinical_meeting.services.transcription import TranscriptionService
from tests.support.fakes import FakeTranscriptionProvider


def test_validate_rejects_exe() -> None:
    service = TranscriptionService(FakeTranscriptionProvider())
    with pytest.raises(ValueError, match="Unsupported audio"):
        service.validate_audio("malware.exe", b"not-audio")


def test_validate_rejects_oversize() -> None:
    service = TranscriptionService(FakeTranscriptionProvider(), max_audio_bytes=10)
    with pytest.raises(ValueError, match="exceeds max size"):
        service.validate_audio("clip.wav", b"x" * 11)


def test_transcribe_to_text_formats_segments() -> None:
    provider = FakeTranscriptionProvider(
        [
            TranscriptSegment(0.0, 1.0, "Alpha"),
            TranscriptSegment(61.0, 62.0, "Beta"),
        ]
    )
    service = TranscriptionService(provider, default_speaker="Speaker")
    text = service.transcribe_to_text("meeting.wav", b"fake-bytes", default_speaker="Nurse")
    assert text == "[00:00:00] Nurse: Alpha\n[00:01:01] Nurse: Beta"
    assert len(provider.calls) == 1


def test_transcribe_empty_speech_raises() -> None:
    provider = FakeTranscriptionProvider([])
    service = TranscriptionService(provider)
    with pytest.raises(ValueError, match="No speech"):
        service.transcribe_to_text("silent.mp3", b"fake")


def test_provider_failure_is_runtime_error() -> None:
    provider = FakeTranscriptionProvider(fail=True)
    service = TranscriptionService(provider)
    with pytest.raises(RuntimeError, match="Transcription failed"):
        service.transcribe_to_text("bad.wav", b"fake")
