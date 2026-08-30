from clinical_meeting.config import (
    build_llm_provider,
    get_settings,
    get_transcription_provider,
)
from clinical_meeting.ports import EmbeddingProvider, LLMProvider, VectorStore
from clinical_meeting.services.answer import AnswerService
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.meeting_intelligence import MeetingIntelligenceService
from clinical_meeting.services.retrieval import RetrievalService
from clinical_meeting.services.transcription import TranscriptionService

_ingestion: IngestionService | None = None
_answer: AnswerService | None = None
_intelligence: MeetingIntelligenceService | None = None
_llm: LLMProvider | None = None
_embedder: EmbeddingProvider | None = None
_store: VectorStore | None = None
_transcription: TranscriptionService | None = None


def _ensure_services() -> None:
    global _ingestion, _answer, _intelligence, _llm, _embedder, _store, _transcription
    if _ingestion is not None:
        return
    settings = get_settings()
    from pathlib import Path

    from clinical_meeting.adapters.storage.meeting_registry import JsonMeetingRegistry
    from clinical_meeting.config import get_embedding_provider, get_vector_store

    _embedder = get_embedding_provider()
    _store = get_vector_store()
    registry = JsonMeetingRegistry(Path(__file__).resolve().parents[3] / "data" / "meetings.json")
    _ingestion = IngestionService(_embedder, _store, settings.max_upload_bytes, registry=registry)
    _retrieval = RetrievalService(
        _embedder, _store, settings.retrieval_top_k, settings.max_context_tokens
    )
    _llm = build_llm_provider(settings)
    _answer = AnswerService(_llm, _retrieval)
    _intelligence = MeetingIntelligenceService(_llm, _retrieval, _ingestion)
    _transcription = TranscriptionService(
        get_transcription_provider(),
        max_audio_bytes=settings.max_audio_upload_bytes,
        default_speaker=settings.transcript_default_speaker,
    )


def override_services(
    ingestion: IngestionService,
    answer: AnswerService,
    intelligence: MeetingIntelligenceService,
    llm: LLMProvider,
    transcription: TranscriptionService | None = None,
) -> None:
    global _ingestion, _answer, _intelligence, _llm, _transcription
    _ingestion = ingestion
    _answer = answer
    _intelligence = intelligence
    _llm = llm
    if transcription is not None:
        _transcription = transcription


def get_ingestion_service() -> IngestionService:
    _ensure_services()
    if _ingestion is None:
        raise RuntimeError("Ingestion service failed to initialize")
    return _ingestion


def get_answer_service() -> AnswerService:
    _ensure_services()
    if _answer is None:
        raise RuntimeError("Answer service failed to initialize")
    return _answer


def get_intelligence_service() -> MeetingIntelligenceService:
    _ensure_services()
    if _intelligence is None:
        raise RuntimeError("Intelligence service failed to initialize")
    return _intelligence


def get_transcription_service() -> TranscriptionService:
    _ensure_services()
    if _transcription is None:
        raise RuntimeError("Transcription service failed to initialize")
    return _transcription


def get_llm_info() -> tuple[str, str]:
    _ensure_services()
    if _llm is None:
        raise RuntimeError("LLM provider failed to initialize")
    return _llm.provider_name, _llm.model_name
