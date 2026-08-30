from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinical_meeting.api import dependencies as deps
from clinical_meeting.api.app import app
from clinical_meeting.domain.models import TranscriptSegment
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.retrieval import RetrievalService
from clinical_meeting.services.transcription import TranscriptionService
from tests.support.fakes import FakeEmbedder, FakeLLM, FakeTranscriptionProvider
from tests.support.memory_store import InMemoryVectorStore


@pytest.fixture
def client() -> TestClient:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    retrieval = RetrievalService(embedder, store)
    llm = FakeLLM()
    answer = AnswerService(llm, retrieval)
    intelligence = MeetingIntelligenceService(llm, retrieval, ingestion)
    transcription = TranscriptionService(
        FakeTranscriptionProvider(
            [
                TranscriptSegment(0.0, 2.0, "We will enroll twenty patients."),
                TranscriptSegment(2.0, 4.0, "Update the protocol today."),
            ]
        )
    )
    deps.override_services(ingestion, answer, intelligence, llm, transcription)
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_upload_and_list(client: TestClient) -> None:
    sample = (
        Path(__file__).resolve().parents[3]
        / "samples"
        / "transcripts"
        / "trial_protocol_review.txt"
    )
    with sample.open("rb") as handle:
        response = client.post(
            "/api/v1/meetings",
            data={"title": "Trial Review"},
            files={"file": ("trial.txt", handle, "text/plain")},
        )
    assert response.status_code == 200
    meeting_id = response.json()["meeting_id"]
    listed = client.get("/api/v1/meetings")
    assert any(m["meeting_id"] == meeting_id for m in listed.json())


def test_upload_from_audio(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meetings/from-audio",
        data={"title": "Audio Review", "default_speaker": "Dr. Chen"},
        files={"file": ("clip.wav", b"fake-audio-bytes", "audio/wav")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Audio Review"
    assert body["turn_count"] == 2
    assert "Dr. Chen" in body["participants"]


def test_upload_from_audio_rejects_bad_suffix(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meetings/from-audio",
        data={"title": "Bad"},
        files={"file": ("clip.exe", b"fake", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_from_audio_model_failure() -> None:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    retrieval = RetrievalService(embedder, store)
    llm = FakeLLM()
    answer = AnswerService(llm, retrieval)
    intelligence = MeetingIntelligenceService(llm, retrieval, ingestion)
    transcription = TranscriptionService(FakeTranscriptionProvider(fail=True))
    deps.override_services(ingestion, answer, intelligence, llm, transcription)
    client = TestClient(app)
    response = client.post(
        "/api/v1/meetings/from-audio",
        data={"title": "Fail"},
        files={"file": ("clip.wav", b"fake", "audio/wav")},
    )
    assert response.status_code == 503
