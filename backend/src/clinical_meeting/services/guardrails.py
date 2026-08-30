import re
from dataclasses import dataclass

from clinical_meeting.domain.models import ActionItem, Citation, Decision, Topic, TranscriptTurn

REFUSAL_PREFIX = "INSUFFICIENT_EVIDENCE"
REFUSAL_PHRASES = (
    "does not contain enough evidence",
    "not found in the transcript",
    "insufficient evidence",
)


@dataclass(frozen=True)
class GuardrailResult:
    answer: str
    refused: bool


def validate_grounded_answer(answer: str, citations: list[Citation]) -> GuardrailResult:
    lower = answer.lower()
    if answer.startswith(REFUSAL_PREFIX) or any(p in lower for p in REFUSAL_PHRASES):
        return GuardrailResult(answer=answer, refused=True)
    if not citations:
        return GuardrailResult(
            answer=(
                "INSUFFICIENT_EVIDENCE: The transcript does not contain enough evidence "
                "to answer this question."
            ),
            refused=True,
        )
    cited_speaker = any(c.speaker.lower() in lower for c in citations)
    cited_time = any(c.timestamp in answer for c in citations)
    if not cited_speaker and not cited_time:
        return GuardrailResult(
            answer=(
                "INSUFFICIENT_EVIDENCE: The transcript does not contain enough evidence "
                "to answer this question."
            ),
            refused=True,
        )
    return GuardrailResult(answer=answer, refused=False)


ACTION_PATTERNS = [
    re.compile(r"action item[:\s—-]+(.+)", re.I),
    re.compile(r"will follow up on (.+)", re.I),
    re.compile(r"by (?:monday|tuesday|wednesday|thursday|friday|eod|tomorrow)", re.I),
]

DECISION_PATTERNS = [
    re.compile(r"we decided (.+)", re.I),
    re.compile(r"agreed to (.+)", re.I),
    re.compile(r"approved (.+)", re.I),
    re.compile(r"decision[:\s—-]+(.+)", re.I),
]

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "we",
    "is",
    "are",
    "was",
    "be",
    "this",
    "that",
    "it",
    "our",
    "will",
    "need",
}


def extract_action_items(turns: list[TranscriptTurn]) -> list[ActionItem]:
    items: list[ActionItem] = []
    for turn in turns:
        lower = turn.text.lower()
        action_hint = (
            "action item" in lower
            or "follow up" in lower
            or "by friday" in lower
            or "by eod" in lower
        )
        if action_hint:
            items.append(
                ActionItem(
                    text=turn.text,
                    assignee=turn.speaker,
                    timestamp=turn.timestamp,
                    speaker=turn.speaker,
                )
            )
            continue
        for pattern in ACTION_PATTERNS:
            if pattern.search(turn.text):
                items.append(
                    ActionItem(
                        text=turn.text,
                        assignee=turn.speaker,
                        timestamp=turn.timestamp,
                        speaker=turn.speaker,
                    )
                )
                break
    return items


def extract_decisions(turns: list[TranscriptTurn]) -> list[Decision]:
    decisions: list[Decision] = []
    for turn in turns:
        for pattern in DECISION_PATTERNS:
            match = pattern.search(turn.text)
            if match:
                decisions.append(
                    Decision(
                        text=match.group(0),
                        timestamp=turn.timestamp,
                        speaker=turn.speaker,
                    )
                )
                break
    return decisions


def extract_topics(turns: list[TranscriptTurn], limit: int = 8) -> list[Topic]:
    counts: dict[str, int] = {}
    for turn in turns:
        for word in re.findall(r"[a-zA-Z]{4,}", turn.text.lower()):
            if word in STOPWORDS:
                continue
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [Topic(name=word, score=float(score)) for word, score in ranked[:limit]]
