import pytest

from clinical_meeting.adapters.loaders.txt_loader import TranscriptParser
from clinical_meeting.services.guardrails import extract_topics
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore

SAMPLE = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def test_extract_topics_returns_keywords() -> None:
    turns = TranscriptParser().parse("m1", SAMPLE)
    topics = extract_topics(turns)
    assert topics
    assert any(t.name in {"enrollment", "consent", "hemoglobin", "form"} for t in topics)


@pytest.mark.asyncio
async def test_meeting_intelligence_summary() -> None:
    embedder = FakeEmbedder()
    store = InMemoryVectorStore()
    ingestion = IngestionService(embedder, store)
    ingestion.ingest("Trial", SAMPLE, meeting_id="intel-1")
    retrieval = RetrievalService(embedder, store)
    intelligence = MeetingIntelligenceService(FakeLLM("Summary text."), retrieval, ingestion)
    participants = intelligence.get_participants("intel-1")
    assert "Dr. Chen" in participants
    decisions = intelligence.get_decisions("intel-1")
    assert decisions
    actions = intelligence.get_action_items("intel-1")
    assert actions
    summary = await intelligence.get_summary("intel-1")
    assert summary


def test_ingestion_validation_rejects_invalid_extension() -> None:
    ingestion = IngestionService(FakeEmbedder(), InMemoryVectorStore())
    with pytest.raises(ValueError, match="Only .txt"):
        ingestion.validate_upload("notes.pdf", b"data")


def test_build_llm_provider_openai_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from clinical_meeting.config import Settings, build_llm_provider

    settings = Settings(llm_provider="openai", openai_api_key="")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_llm_provider(settings)
