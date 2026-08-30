import pytest

from clinical_meeting.adapters.loaders.txt_loader import TranscriptParser

SAMPLE = """
[00:01:23] Dr. Chen: We need to finalize the enrollment criteria for Trial A-102.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def test_parser_extracts_turns() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    assert len(turns) == 2
    assert turns[0].speaker == "Dr. Chen"
    assert turns[0].timestamp == "00:01:23"
    assert turns[0].turn_index == 0
    assert turns[1].turn_index == 1


def test_parser_rejects_invalid_line() -> None:
    with pytest.raises(ValueError, match="Invalid transcript line"):
        TranscriptParser().parse("m1", "Dr. Chen: missing timestamp")
