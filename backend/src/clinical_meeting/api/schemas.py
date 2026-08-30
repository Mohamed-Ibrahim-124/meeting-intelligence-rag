from datetime import datetime

from pydantic import BaseModel, Field


class MeetingCreateResponse(BaseModel):
    meeting_id: str
    title: str
    turn_count: int
    chunk_count: int
    participants: list[str]


class MeetingSummary(BaseModel):
    meeting_id: str
    title: str
    uploaded_at: datetime
    turn_count: int
    chunk_count: int
    participants: list[str]


class CitationSchema(BaseModel):
    speaker: str
    timestamp: str
    snippet: str
    chunk_id: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    speaker: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationSchema]
    refused: bool
    llm_provider: str
    model_name: str


class ActionItemSchema(BaseModel):
    text: str
    assignee: str | None
    timestamp: str
    speaker: str


class DecisionSchema(BaseModel):
    text: str
    timestamp: str
    speaker: str


class TopicSchema(BaseModel):
    name: str
    score: float


class TranscriptTurnSchema(BaseModel):
    timestamp: str
    speaker: str
    text: str
    turn_index: int


class MeetingDetailResponse(BaseModel):
    meeting: MeetingSummary
    turns: list[TranscriptTurnSchema]
