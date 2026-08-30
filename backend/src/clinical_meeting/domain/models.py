from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TranscriptSegment:
    """Timed ASR segment before conversion to transcript lines."""

    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class TranscriptTurn:
    meeting_id: str
    timestamp: str
    speaker: str
    text: str
    turn_index: int


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    meeting_id: str
    text: str
    speaker: str
    start_time: str
    end_time: str
    chunk_index: int
    turn_index_start: int
    turn_index_end: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    speaker: str
    timestamp: str
    snippet: str
    chunk_id: str


@dataclass
class MeetingMetadata:
    meeting_id: str
    title: str
    uploaded_at: datetime
    turn_count: int
    chunk_count: int
    participants: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ActionItem:
    text: str
    assignee: str | None
    timestamp: str
    speaker: str


@dataclass(frozen=True)
class Decision:
    text: str
    timestamp: str
    speaker: str


@dataclass(frozen=True)
class Topic:
    name: str
    score: float


@dataclass(frozen=True)
class QueryResult:
    answer: str
    citations: list[Citation]
    refused: bool = False


@dataclass(frozen=True)
class LLMResponse:
    text: str
    token_usage: int | None = None
