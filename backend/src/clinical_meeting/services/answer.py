from clinical_meeting.domain.models import Citation, QueryResult, RetrievedChunk
from clinical_meeting.ports import LLMProvider
from clinical_meeting.services.guardrails import validate_grounded_answer
from clinical_meeting.services.retrieval import RetrievalService

ANSWER_SYSTEM_PROMPT = (
    "You answer questions about clinical meeting transcripts using ONLY the provided context. "
    "Always cite speakers and timestamps from the context. "
    "If the context does not contain enough evidence, respond exactly with: "
    "INSUFFICIENT_EVIDENCE: The transcript does not contain enough evidence "
    "to answer this question."
)


class AnswerService:
    def __init__(self, llm: LLMProvider, retrieval_service: RetrievalService) -> None:
        self._llm = llm
        self._retrieval = retrieval_service

    async def answer(
        self,
        meeting_id: str,
        question: str,
        speaker: str | None = None,
    ) -> QueryResult:
        speaker_filter = speaker or self._retrieval.extract_speaker_filter(question)
        chunks = self._retrieval.retrieve(meeting_id, question, speaker_filter)
        if not chunks:
            return QueryResult(
                answer=(
                    "INSUFFICIENT_EVIDENCE: The transcript does not contain enough evidence "
                    "to answer this question."
                ),
                citations=[],
                refused=True,
            )
        context = self._retrieval.build_context(chunks)
        user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer with citations."
        response = await self._llm.complete(ANSWER_SYSTEM_PROMPT, user_prompt)
        citations = self._build_citations(chunks)
        validated = validate_grounded_answer(response.text, citations)
        return QueryResult(answer=validated.answer, citations=citations, refused=validated.refused)

    @staticmethod
    def _build_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
        citations: list[Citation] = []
        for item in chunks:
            chunk = item.chunk
            snippet = chunk.text[:200] + ("..." if len(chunk.text) > 200 else "")
            citations.append(
                Citation(
                    speaker=chunk.speaker,
                    timestamp=chunk.start_time,
                    snippet=snippet,
                    chunk_id=chunk.chunk_id,
                )
            )
        return citations
