from clinical_meeting.domain.models import Chunk
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder
from tests.support.memory_store import InMemoryVectorStore


def test_retrieval_returns_relevant_chunk() -> None:
    store = InMemoryVectorStore()
    chunk = Chunk(
        chunk_id="c1",
        meeting_id="m1",
        text="Trial A-102 enrollment criteria",
        speaker="Dr. Chen",
        start_time="00:01:23",
        end_time="00:01:23",
        chunk_index=0,
        turn_index_start=0,
        turn_index_end=0,
    )
    store.upsert_chunks("m1", [chunk], [[10.0, 1.0, 0.5]])
    service = RetrievalService(FakeEmbedder(), store, top_k=1)
    results = service.retrieve("m1", "enrollment criteria Trial A-102")
    assert len(results) == 1
    assert "Trial A-102" in results[0].chunk.text


def test_query_normalization_expands_abbreviation() -> None:
    service = RetrievalService(FakeEmbedder(), InMemoryVectorStore())
    assert "doctor" in service.normalize_query("What did Dr say?")
