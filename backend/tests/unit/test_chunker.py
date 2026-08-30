from clinical_meeting.adapters.chunking.speaker_turn_chunker import SpeakerTurnChunker
from clinical_meeting.adapters.loaders.txt_loader import TranscriptParser

SAMPLE = """
[00:01:23] Dr. Chen: Short line one.
[00:01:24] Dr. Chen: Short line two.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def test_chunker_merges_short_same_speaker_turns() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    chunks = SpeakerTurnChunker().chunk(turns)
    assert len(chunks) == 2
    assert chunks[0].speaker == "Dr. Chen"
    assert "Short line one" in chunks[0].text
    assert "Short line two" in chunks[0].text
    assert chunks[0].start_time == "00:01:23"
    assert chunks[0].end_time == "00:01:24"


def test_chunk_metadata_fields() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    chunks = SpeakerTurnChunker().chunk(turns)
    chunk = chunks[1]
    assert chunk.chunk_index == 1
    assert chunk.turn_index_start <= chunk.turn_index_end
    assert chunk.meeting_id == "m1"


def test_chunker_splits_long_turns() -> None:
    long_text = "Sentence one. " + "Word " * 500
    sample = f"[00:02:00] Dr. Chen: {long_text}"
    turns = TranscriptParser().parse("m-long", sample)
    chunks = SpeakerTurnChunker().chunk(turns)
    assert len(chunks) > 1
