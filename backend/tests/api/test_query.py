import pytest
from fastapi.testclient import TestClient

from clinical_meeting.api import dependencies as deps
from clinical_meeting.api.app import app
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore


@pytest.fixture
def seeded_client() -> TestClient:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    metadata = ingestion.ingest(
        "Trial Review",
        "[00:01:23] Dr. Chen: We finalized enrollment criteria for Trial A-102.\n",
        meeting_id="m-test",
    )
    assert metadata.meeting_id == "m-test"
    retrieval = RetrievalService(embedder, store)
    llm = FakeLLM("Dr. Chen finalized enrollment criteria for Trial A-102 at 00:01:23.")
    answer = AnswerService(llm, retrieval)
    intelligence = MeetingIntelligenceService(llm, retrieval, ingestion)
    deps.override_services(ingestion, answer, intelligence, llm)
    return TestClient(app)


def test_query_returns_citations(seeded_client: TestClient) -> None:
    response = seeded_client.post(
        "/api/v1/meetings/m-test/query",
        json={"question": "What did Dr. Chen say about enrollment?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert body["citations"][0]["speaker"] == "Dr. Chen"
