from clinical_meeting.domain.models import Citation
from clinical_meeting.services.guardrails import validate_grounded_answer


def test_refusal_when_no_citations() -> None:
    result = validate_grounded_answer("Some answer without grounding.", [])
    assert result.refused is True


def test_accepts_answer_with_speaker_reference() -> None:
    citations = [Citation(speaker="Dr. Chen", timestamp="00:01:23", snippet="text", chunk_id="c1")]
    result = validate_grounded_answer("Dr. Chen noted the enrollment criteria.", citations)
    assert result.refused is False


def test_refusal_prefix_detected() -> None:
    result = validate_grounded_answer(
        "INSUFFICIENT_EVIDENCE: The transcript does not contain enough evidence.",
        [],
    )
    assert result.refused is True
