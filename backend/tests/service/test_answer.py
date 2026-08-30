import pytest

from clinical_meeting.domain.models import Chunk
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.retrieval import RetrievalService
from tests.support.fakes import FakeEmbedder, FakeLLM
from tests.support.memory_store import InMemoryVectorStore


@pytest.mark.asyncio
async def test_answer_returns_citations() -> None:
    store = InMemoryVectorStore()
    chunk = Chunk(
        chunk_id="c1",
        meeting_id="m1",
        text="Dr. Chen finalized enrollment criteria for Trial A-102.",
        speaker="Dr. Chen",
        start_time="00:01:23",
        end_time="00:01:23",
        chunk_index=0,
        turn_index_start=0,
        turn_index_end=0,
    )
    store.upsert_chunks("m1", [chunk], [[20.0, 1.0, 0.5]])
    retrieval = RetrievalService(FakeEmbedder(), store, top_k=1)
    answer = AnswerService(FakeLLM(), retrieval)
    result = await answer.answer("m1", "What did Dr. Chen say about enrollment?")
    assert result.citations
    assert result.citations[0].speaker == "Dr. Chen"


@pytest.mark.asyncio
async def test_answer_refuses_without_chunks() -> None:
    retrieval = RetrievalService(FakeEmbedder(), InMemoryVectorStore(), top_k=1)
    answer = AnswerService(FakeLLM(), retrieval)
    result = await answer.answer("missing", "What about budgets?")
    assert result.refused is True
