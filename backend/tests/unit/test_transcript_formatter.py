from clinical_meeting.domain.models import TranscriptSegment
from clinical_meeting.services.transcript_formatter import format_timestamp, segments_to_transcript


def test_format_timestamp() -> None:
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(65) == "00:01:05"
    assert format_timestamp(3661) == "01:01:01"


def test_segments_to_transcript_exact() -> None:
    segments = [
        TranscriptSegment(0.0, 1.5, "Hello team."),
        TranscriptSegment(90.0, 95.0, "  Next topic.  "),
        TranscriptSegment(100.0, 101.0, "   "),
    ]
    text = segments_to_transcript(segments, "Dr. Chen")
    assert text == ("[00:00:00] Dr. Chen: Hello team.\n[00:01:30] Dr. Chen: Next topic.")
