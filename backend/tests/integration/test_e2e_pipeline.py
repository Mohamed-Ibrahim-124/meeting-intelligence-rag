import pytest

from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore

TRANSCRIPT = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment in Trial A-102.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


@pytest.mark.asyncio
async def test_e2e_ingest_query_citations() -> None:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    ingestion.ingest("Trial", TRANSCRIPT, meeting_id="e2e-1")
    retrieval = RetrievalService(embedder, store, top_k=2)
    answer = AnswerService(
        FakeLLM("Dr. Chen decided hemoglobin above 11 g/dL at 00:01:03."),
        retrieval,
    )
    result = await answer.answer("e2e-1", "What enrollment lab threshold was decided?")
    assert result.citations
    assert any(c.speaker == "Dr. Chen" for c in result.citations)


@pytest.mark.asyncio
async def test_citation_regression_action_item_question() -> None:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    ingestion.ingest("Trial", TRANSCRIPT, meeting_id="e2e-2")
    retrieval = RetrievalService(embedder, store, top_k=2)
    answer = AnswerService(
        FakeLLM("Nurse Patel has an action item about the consent form at 00:01:45."),
        retrieval,
    )
    result = await answer.answer("e2e-2", "What action item did Nurse Patel mention?")
    assert result.citations
    assert result.citations[0].speaker == "Nurse Patel"
    assert result.citations[0].timestamp == "00:01:45"
