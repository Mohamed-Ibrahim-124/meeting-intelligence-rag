import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from clinical_meeting.domain.models import Chunk, RetrievedChunk


class QdrantAdapter:
    def __init__(self, url: str, collection: str, vector_size: int) -> None:
        self._client = QdrantClient(url=url)
        self._collection = collection
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        names = [c.name for c in self._client.get_collections().collections]
        if self._collection not in names:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qmodels.VectorParams(
                    size=vector_size, distance=qmodels.Distance.COSINE
                ),
            )

    def upsert_chunks(
        self, meeting_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None:
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            points.append(
                qmodels.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                    vector=vector,
                    payload={
                        "meeting_id": meeting_id,
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "speaker": chunk.speaker,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                        "chunk_index": chunk.chunk_index,
                        "turn_index_start": chunk.turn_index_start,
                        "turn_index_end": chunk.turn_index_end,
                    },
                )
            )
        self._client.upsert(collection_name=self._collection, points=points)

    def search(
        self,
        meeting_id: str,
        query_vector: list[float],
        top_k: int,
        speaker: str | None = None,
    ) -> list[RetrievedChunk]:
        filters: list[qmodels.FieldCondition] = [
            qmodels.FieldCondition(
                key="meeting_id",
                match=qmodels.MatchValue(value=meeting_id),
            )
        ]
        if speaker:
            filters.append(
                qmodels.FieldCondition(
                    key="speaker",
                    match=qmodels.MatchValue(value=speaker),
                )
            )
        query_filter = qmodels.Filter(must=filters)  # type: ignore[arg-type]
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        retrieved: list[RetrievedChunk] = []
        for hit in response.points:
            payload = hit.payload or {}
            chunk = Chunk(
                chunk_id=str(payload.get("chunk_id", "")),
                meeting_id=str(payload.get("meeting_id", meeting_id)),
                text=str(payload.get("text", "")),
                speaker=str(payload.get("speaker", "")),
                start_time=str(payload.get("start_time", "")),
                end_time=str(payload.get("end_time", "")),
                chunk_index=int(payload.get("chunk_index", 0)),
                turn_index_start=int(payload.get("turn_index_start", 0)),
                turn_index_end=int(payload.get("turn_index_end", 0)),
            )
            retrieved.append(RetrievedChunk(chunk=chunk, score=float(hit.score or 0.0)))
        return retrieved

    def delete_meeting(self, meeting_id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="meeting_id",
                            match=qmodels.MatchValue(value=meeting_id),
                        )
                    ]
                )
            ),
        )

    def list_meetings(self) -> list[str]:
        meetings: set[str] = set()
        offset = None
        while True:
            records, offset = self._client.scroll(
                collection_name=self._collection,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                meeting_id = payload.get("meeting_id")
                if meeting_id:
                    meetings.add(str(meeting_id))
            if offset is None:
                break
        return sorted(meetings)

    def get_meeting_chunks(self, meeting_id: str) -> list[Chunk]:
        chunks: list[Chunk] = []
        offset = None
        while True:
            records, offset = self._client.scroll(
                collection_name=self._collection,
                limit=100,
                offset=offset,
                scroll_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="meeting_id",
                            match=qmodels.MatchValue(value=meeting_id),
                        )
                    ]
                ),
                with_payload=True,
                with_vectors=False,
            )
            for record in records:
                payload = record.payload or {}
                chunks.append(
                    Chunk(
                        chunk_id=str(payload.get("chunk_id", "")),
                        meeting_id=meeting_id,
                        text=str(payload.get("text", "")),
                        speaker=str(payload.get("speaker", "")),
                        start_time=str(payload.get("start_time", "")),
                        end_time=str(payload.get("end_time", "")),
                        chunk_index=int(payload.get("chunk_index", 0)),
                        turn_index_start=int(payload.get("turn_index_start", 0)),
                        turn_index_end=int(payload.get("turn_index_end", 0)),
                    )
                )
            if offset is None:
                break
        return sorted(chunks, key=lambda c: c.chunk_index)
