"""Convert ASR segments into ingestible transcript text."""

from __future__ import annotations

from clinical_meeting.constants import SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from clinical_meeting.domain.models import TranscriptSegment


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours = total // SECONDS_PER_HOUR
    minutes = (total % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE
    secs = total % SECONDS_PER_MINUTE
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def segments_to_transcript(
    segments: list[TranscriptSegment],
    default_speaker: str,
) -> str:
    lines: list[str] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        stamp = format_timestamp(segment.start_seconds)
        lines.append(f"[{stamp}] {default_speaker}: {text}")
    return "\n".join(lines)
