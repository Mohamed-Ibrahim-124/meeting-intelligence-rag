from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from clinical_meeting.api.dependencies import (
    get_answer_service,
    get_ingestion_service,
    get_intelligence_service,
    get_llm_info,
    get_transcription_service,
)
from clinical_meeting.api.schemas import (
    ActionItemSchema,
    CitationSchema,
    DecisionSchema,
    MeetingCreateResponse,
    MeetingDetailResponse,
    MeetingSummary,
    QueryRequest,
    QueryResponse,
    TopicSchema,
    TranscriptTurnSchema,
)
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.transcription import TranscriptionService

router = APIRouter(prefix="/api/v1/meetings", tags=["meetings"])


@router.post("", response_model=MeetingCreateResponse)
async def upload_meeting(
    title: str = Form(...),
    file: UploadFile = File(...),
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> MeetingCreateResponse:
    content = await file.read()
    try:
        ingestion.validate_upload(file.filename or "transcript.txt", content)
        metadata = ingestion.ingest(title, content.decode("utf-8"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MeetingCreateResponse(
        meeting_id=metadata.meeting_id,
        title=metadata.title,
        turn_count=metadata.turn_count,
        chunk_count=metadata.chunk_count,
        participants=metadata.participants,
    )


@router.post("/from-audio", response_model=MeetingCreateResponse)
async def upload_meeting_from_audio(
    title: str = Form(...),
    file: UploadFile = File(...),
    default_speaker: str | None = Form(None),
    ingestion: IngestionService = Depends(get_ingestion_service),
    transcription: TranscriptionService = Depends(get_transcription_service),
) -> MeetingCreateResponse:
    content = await file.read()
    try:
        transcript = transcription.transcribe_to_text(
            file.filename or "audio.wav",
            content,
            default_speaker=default_speaker,
            content_type=file.content_type,
        )
        metadata = ingestion.ingest(title, transcript)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return MeetingCreateResponse(
        meeting_id=metadata.meeting_id,
        title=metadata.title,
        turn_count=metadata.turn_count,
        chunk_count=metadata.chunk_count,
        participants=metadata.participants,
    )


@router.get("", response_model=list[MeetingSummary])
def list_meetings(
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> list[MeetingSummary]:
    return [
        MeetingSummary(
            meeting_id=m.meeting_id,
            title=m.title,
            uploaded_at=m.uploaded_at,
            turn_count=m.turn_count,
            chunk_count=m.chunk_count,
            participants=m.participants,
        )
        for m in ingestion.list_metadata()
    ]


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
def get_meeting(
    meeting_id: str,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> MeetingDetailResponse:
    metadata = ingestion.get_metadata(meeting_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Meeting not found")
    turns = ingestion.get_turns(meeting_id)
    return MeetingDetailResponse(
        meeting=MeetingSummary(
            meeting_id=metadata.meeting_id,
            title=metadata.title,
            uploaded_at=metadata.uploaded_at,
            turn_count=metadata.turn_count,
            chunk_count=metadata.chunk_count,
            participants=metadata.participants,
        ),
        turns=[
            TranscriptTurnSchema(
                timestamp=t.timestamp,
                speaker=t.speaker,
                text=t.text,
                turn_index=t.turn_index,
            )
            for t in turns
        ],
    )


@router.post("/{meeting_id}/query", response_model=QueryResponse)
async def query_meeting(
    meeting_id: str,
    body: QueryRequest,
    answer_service: AnswerService = Depends(get_answer_service),
) -> QueryResponse:
    provider, model = get_llm_info()
    result = await answer_service.answer(meeting_id, body.question, body.speaker)
    return QueryResponse(
        answer=result.answer,
        citations=[
            CitationSchema(
                speaker=c.speaker,
                timestamp=c.timestamp,
                snippet=c.snippet,
                chunk_id=c.chunk_id,
            )
            for c in result.citations
        ],
        refused=result.refused,
        llm_provider=provider,
        model_name=model,
    )


@router.get("/{meeting_id}/summary")
async def meeting_summary(
    meeting_id: str,
    intelligence: MeetingIntelligenceService = Depends(get_intelligence_service),
) -> dict[str, str]:
    summary = await intelligence.get_summary(meeting_id)
    return {"summary": summary}


@router.get("/{meeting_id}/decisions", response_model=list[DecisionSchema])
def meeting_decisions(
    meeting_id: str,
    intelligence: MeetingIntelligenceService = Depends(get_intelligence_service),
) -> list[DecisionSchema]:
    return [
        DecisionSchema(text=d.text, timestamp=d.timestamp, speaker=d.speaker)
        for d in intelligence.get_decisions(meeting_id)
    ]


@router.get("/{meeting_id}/action-items", response_model=list[ActionItemSchema])
def meeting_action_items(
    meeting_id: str,
    intelligence: MeetingIntelligenceService = Depends(get_intelligence_service),
) -> list[ActionItemSchema]:
    return [
        ActionItemSchema(
            text=a.text,
            assignee=a.assignee,
            timestamp=a.timestamp,
            speaker=a.speaker,
        )
        for a in intelligence.get_action_items(meeting_id)
    ]


@router.get("/{meeting_id}/topics", response_model=list[TopicSchema])
def meeting_topics(
    meeting_id: str,
    intelligence: MeetingIntelligenceService = Depends(get_intelligence_service),
) -> list[TopicSchema]:
    return [TopicSchema(name=t.name, score=t.score) for t in intelligence.get_topics(meeting_id)]


@router.get("/{meeting_id}/participants", response_model=list[str])
def meeting_participants(
    meeting_id: str,
    intelligence: MeetingIntelligenceService = Depends(get_intelligence_service),
) -> list[str]:
    return intelligence.get_participants(meeting_id)
