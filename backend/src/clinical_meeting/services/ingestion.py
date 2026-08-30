import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from clinical_meeting.adapters.chunking.speaker_turn_chunker import SpeakerTurnChunker
from clinical_meeting.adapters.loaders.txt_loader import TxtTranscriptLoader
from clinical_meeting.adapters.storage.meeting_registry import JsonMeetingRegistry
from clinical_meeting.constants import ALLOWED_TEXT_SUFFIXES, DEFAULT_MAX_TEXT_UPLOAD_BYTES
from clinical_meeting.domain.models import Chunk, MeetingMetadata, TranscriptTurn
from clinical_meeting.ports import EmbeddingProvider, VectorStore

SUSPICIOUS_PATTERN = re.compile(r"(<\?php|<script|exec\(|eval\()", re.IGNORECASE)


class IngestionService:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: VectorStore,
        max_upload_bytes: int = DEFAULT_MAX_TEXT_UPLOAD_BYTES,
        registry: JsonMeetingRegistry | None = None,
    ) -> None:
        self._embedder = embedder
        self._store = store
        self._loader = TxtTranscriptLoader()
        self._chunker = SpeakerTurnChunker()
        self._max_upload_bytes = max_upload_bytes
        self._registry = registry or JsonMeetingRegistry(Path("data") / "meetings.json")
        self._metadata: dict[str, MeetingMetadata] = {}
        self._turns: dict[str, list[TranscriptTurn]] = {}
        self._hydrate_from_registry()

    def _hydrate_from_registry(self) -> None:
        for meta in self._registry.list_metadata():
            self._metadata[meta.meeting_id] = meta
            self._turns[meta.meeting_id] = self._registry.get_turns(meta.meeting_id)

    def validate_upload(self, filename: str, content: bytes) -> None:
        if len(content) > self._max_upload_bytes:
            raise ValueError(f"File exceeds max size of {self._max_upload_bytes} bytes")
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_TEXT_SUFFIXES:
            raise ValueError("Only .txt transcript files are supported")
        text = content.decode("utf-8")
        if SUSPICIOUS_PATTERN.search(text):
            raise ValueError("File contains disallowed content")

    def ingest(self, title: str, content: str, meeting_id: str | None = None) -> MeetingMetadata:
        mid = meeting_id or str(uuid.uuid4())
        turns = self._loader.load_text(mid, content)
        chunks = self._chunker.chunk(turns)
        vectors = self._embedder.embed([c.text for c in chunks])
        self._store.delete_meeting(mid)
        self._store.upsert_chunks(mid, chunks, vectors)
        participants = sorted({t.speaker for t in turns})
        metadata = MeetingMetadata(
            meeting_id=mid,
            title=title,
            uploaded_at=datetime.now(tz=UTC),
            turn_count=len(turns),
            chunk_count=len(chunks),
            participants=participants,
        )
        self._metadata[mid] = metadata
        self._turns[mid] = turns
        self._registry.save_meeting(metadata, turns)
        return metadata

    def get_metadata(self, meeting_id: str) -> MeetingMetadata | None:
        if meeting_id in self._metadata:
            return self._metadata[meeting_id]
        restored = self._restore_from_store(meeting_id)
        return restored

    def list_metadata(self) -> list[MeetingMetadata]:
        store_ids = set(self._store.list_meetings())
        known_ids = (
            set(self._metadata.keys())
            | store_ids
            | {m.meeting_id for m in self._registry.list_metadata()}
        )
        result: list[MeetingMetadata] = []
        for mid in sorted(known_ids):
            meta = self.get_metadata(mid)
            if meta:
                result.append(meta)
        return result

    def get_turns(self, meeting_id: str) -> list[TranscriptTurn]:
        if meeting_id in self._turns:
            return self._turns[meeting_id]
        self._restore_from_store(meeting_id)
        return self._turns.get(meeting_id, [])

    def register_turns(self, meeting_id: str, turns: list[TranscriptTurn]) -> None:
        self._turns[meeting_id] = turns

    def _restore_from_store(self, meeting_id: str) -> MeetingMetadata | None:
        registry_meta = self._registry.get_metadata(meeting_id)
        if registry_meta:
            self._metadata[meeting_id] = registry_meta
            self._turns[meeting_id] = self._registry.get_turns(meeting_id)
            return registry_meta

        chunks = self._store.get_meeting_chunks(meeting_id)
        if not chunks:
            return None
        turns = _turns_from_chunks(meeting_id, chunks)
        participants = sorted({t.speaker for t in turns if t.speaker != "Multiple"})
        metadata = MeetingMetadata(
            meeting_id=meeting_id,
            title=f"Recovered meeting {meeting_id[:8]}",
            uploaded_at=datetime.now(tz=UTC),
            turn_count=len(turns),
            chunk_count=len(chunks),
            participants=participants,
        )
        self._metadata[meeting_id] = metadata
        self._turns[meeting_id] = turns
        self._registry.save_meeting(metadata, turns)
        return metadata


def _turns_from_chunks(meeting_id: str, chunks: list[Chunk]) -> list[TranscriptTurn]:
    turns: list[TranscriptTurn] = []
    for chunk in chunks:
        turns.append(
            TranscriptTurn(
                meeting_id=meeting_id,
                timestamp=chunk.start_time,
                speaker=chunk.speaker,
                text=chunk.text,
                turn_index=chunk.turn_index_start,
            )
        )
    return turns
