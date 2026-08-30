from clinical_meeting.domain.models import Chunk, RetrievedChunk


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: dict[str, list[tuple[Chunk, list[float]]]] = {}

    def upsert_chunks(
        self, meeting_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None:
        self._chunks[meeting_id] = list(zip(chunks, vectors, strict=True))

    def search(
        self,
        meeting_id: str,
        query_vector: list[float],
        top_k: int,
        speaker: str | None = None,
    ) -> list[RetrievedChunk]:
        items = self._chunks.get(meeting_id, [])
        scored: list[RetrievedChunk] = []
        for chunk, vector in items:
            if speaker and chunk.speaker != speaker:
                continue
            score = _cosine(query_vector, vector)
            scored.append(RetrievedChunk(chunk=chunk, score=score))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def delete_meeting(self, meeting_id: str) -> None:
        self._chunks.pop(meeting_id, None)

    def list_meetings(self) -> list[str]:
        return sorted(self._chunks.keys())

    def get_meeting_chunks(self, meeting_id: str) -> list[Chunk]:
        items = self._chunks.get(meeting_id, [])
        return [chunk for chunk, _ in items]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
