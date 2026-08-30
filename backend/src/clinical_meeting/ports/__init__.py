from pathlib import Path
from typing import Protocol

from clinical_meeting.domain.models import (
    Chunk,
    LLMResponse,
    RetrievedChunk,
    TranscriptSegment,
)


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    def dimension(self) -> int: ...


class VectorStore(Protocol):
    def upsert_chunks(
        self, meeting_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None: ...

    def search(
        self,
        meeting_id: str,
        query_vector: list[float],
        top_k: int,
        speaker: str | None = None,
    ) -> list[RetrievedChunk]: ...

    def delete_meeting(self, meeting_id: str) -> None: ...

    def list_meetings(self) -> list[str]: ...

    def get_meeting_chunks(self, meeting_id: str) -> list[Chunk]: ...


class LLMProvider(Protocol):
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse: ...

    @property
    def provider_name(self) -> str: ...

    @property
    def model_name(self) -> str: ...


class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: Path) -> list[TranscriptSegment]: ...

    @property
    def model_name(self) -> str: ...
