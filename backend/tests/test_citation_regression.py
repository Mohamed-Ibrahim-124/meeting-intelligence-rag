import pytest

from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore

TRANSCRIPT = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


GOLDEN = [
    ("e2e-reg-1", "What lab threshold was decided?", "Dr. Chen"),
    ("e2e-reg-2", "What action item did Nurse Patel mention?", "Nurse Patel"),
]


@pytest.mark.parametrize(("meeting_id", "question", "expected_speaker"), GOLDEN)
@pytest.mark.asyncio
async def test_citation_speaker_regression(
    meeting_id: str, question: str, expected_speaker: str
) -> None:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    ingestion.ingest("Trial", TRANSCRIPT, meeting_id=meeting_id)
    retrieval = RetrievalService(embedder, store, top_k=2)
    answer = AnswerService(
        FakeLLM(f"{expected_speaker} provided the relevant update at 00:01:03."),
        retrieval,
    )
    result = await answer.answer(meeting_id, question)
    assert result.citations
    assert any(c.speaker == expected_speaker for c in result.citations)
