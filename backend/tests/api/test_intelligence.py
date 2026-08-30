from fastapi.testclient import TestClient

from clinical_meeting.api import dependencies as deps
from clinical_meeting.api.app import app
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore

SAMPLE = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def _client_with_meeting(meeting_id: str = "api-intel") -> TestClient:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    ingestion.ingest("Trial", SAMPLE, meeting_id=meeting_id)
    retrieval = RetrievalService(embedder, store)
    llm = FakeLLM("Summary.")
    deps.override_services(
        ingestion,
        AnswerService(llm, retrieval),
        MeetingIntelligenceService(llm, retrieval, ingestion),
        llm,
    )
    return TestClient(app)


def test_meeting_not_found() -> None:
    client = _client_with_meeting()
    response = client.get("/api/v1/meetings/does-not-exist")
    assert response.status_code == 404


def test_intelligence_endpoints() -> None:
    client = _client_with_meeting()
    meeting_id = "api-intel"
    assert client.get(f"/api/v1/meetings/{meeting_id}/participants").status_code == 200
    assert client.get(f"/api/v1/meetings/{meeting_id}/decisions").json()
    assert client.get(f"/api/v1/meetings/{meeting_id}/action-items").json()
    assert client.get(f"/api/v1/meetings/{meeting_id}/topics").json()
    assert client.get(f"/api/v1/meetings/{meeting_id}/summary").status_code == 200
