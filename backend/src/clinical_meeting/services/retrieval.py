import re

from clinical_meeting.domain.models import RetrievedChunk
from clinical_meeting.ports import EmbeddingProvider, VectorStore

ABBREVIATIONS = {
    "dr": "doctor",
    "pt": "patient",
    "rx": "prescription",
}


class RetrievalService:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: VectorStore,
        top_k: int = 5,
        max_context_tokens: int = 3000,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._top_k = top_k
        self._max_context_tokens = max_context_tokens

    def normalize_query(self, query: str) -> str:
        normalized = query.strip().lower()
        tokens = normalized.split()
        expanded = [ABBREVIATIONS.get(token, token) for token in tokens]
        return " ".join(expanded)

    def retrieve(
        self,
        meeting_id: str,
        query: str,
        speaker: str | None = None,
    ) -> list[RetrievedChunk]:
        normalized = self.normalize_query(query)
        vector = self._embedder.embed([normalized])[0]
        return self._store.search(meeting_id, vector, self._top_k, speaker)

    def build_context(self, chunks: list[RetrievedChunk]) -> str:
        lines: list[str] = []
        token_budget = self._max_context_tokens * 4
        used = 0
        for index, item in enumerate(chunks, start=1):
            chunk = item.chunk
            header = f"[{index}] {chunk.speaker} @ {chunk.start_time}"
            body = f"{header}\n{chunk.text}"
            if used + len(body) > token_budget:
                break
            lines.append(body)
            used += len(body)
        return "\n\n".join(lines)

    @staticmethod
    def extract_speaker_filter(query: str) -> str | None:
        match = re.search(r"(?:what did|said by|from)\s+([A-Za-z.\s]+?)(?:\?|$| say)", query, re.I)
        if match:
            return match.group(1).strip()
        return None
