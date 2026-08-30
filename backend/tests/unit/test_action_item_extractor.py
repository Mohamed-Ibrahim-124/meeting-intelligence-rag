from clinical_meeting.adapters.loaders.txt_loader import TranscriptParser
from clinical_meeting.services.guardrails import extract_action_items, extract_decisions

SAMPLE = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def test_extract_action_items() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    items = extract_action_items(turns)
    assert len(items) == 1
    assert "consent form" in items[0].text.lower()


def test_extract_decisions() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    decisions = extract_decisions(turns)
    assert len(decisions) == 1
    assert "decided" in decisions[0].text.lower()
