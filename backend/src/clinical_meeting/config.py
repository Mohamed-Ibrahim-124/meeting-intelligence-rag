from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from clinical_meeting.adapters.embeddings.local_st import LocalSentenceTransformerAdapter
from clinical_meeting.adapters.llm.providers import AnthropicAdapter, OllamaAdapter, OpenAIAdapter
from clinical_meeting.adapters.transcription.faster_whisper_adapter import FasterWhisperAdapter
from clinical_meeting.adapters.vector.qdrant_adapter import QdrantAdapter
from clinical_meeting.constants import (
    DEFAULT_MAX_AUDIO_UPLOAD_BYTES,
    DEFAULT_MAX_TEXT_UPLOAD_BYTES,
    DEFAULT_TRANSCRIPT_SPEAKER,
    DEFAULT_WHISPER_COMPUTE_TYPE,
    DEFAULT_WHISPER_DEVICE,
    DEFAULT_WHISPER_MODEL_SIZE,
    WHISPER_COMPUTE_TYPES,
    WHISPER_DEVICES,
    WHISPER_MODEL_SIZES,
)
from clinical_meeting.ports import (
    EmbeddingProvider,
    LLMProvider,
    TranscriptionProvider,
    VectorStore,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "meeting_chunks"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"
    retrieval_top_k: int = 5
    max_context_tokens: int = 3000
    max_upload_bytes: int = DEFAULT_MAX_TEXT_UPLOAD_BYTES
    max_audio_upload_bytes: int = DEFAULT_MAX_AUDIO_UPLOAD_BYTES
    whisper_model_size: str = DEFAULT_WHISPER_MODEL_SIZE
    whisper_device: str = DEFAULT_WHISPER_DEVICE
    whisper_compute_type: str = DEFAULT_WHISPER_COMPUTE_TYPE
    transcript_default_speaker: str = DEFAULT_TRANSCRIPT_SPEAKER
    log_level: str = "INFO"

    @field_validator("whisper_model_size")
    @classmethod
    def _validate_whisper_size(_cls, value: str) -> str:
        # Named Hub sizes, or a local directory (offline / pre-downloaded cache).
        from pathlib import Path

        if value in WHISPER_MODEL_SIZES or Path(value).is_dir():
            return value
        allowed = ", ".join(sorted(WHISPER_MODEL_SIZES))
        raise ValueError(
            f"whisper_model_size must be one of: {allowed}, or an existing model directory"
        )

    @field_validator("whisper_device")
    @classmethod
    def _validate_whisper_device(_cls, value: str) -> str:
        if value not in WHISPER_DEVICES:
            allowed = ", ".join(sorted(WHISPER_DEVICES))
            raise ValueError(f"whisper_device must be one of: {allowed}")
        return value

    @field_validator("whisper_compute_type")
    @classmethod
    def _validate_whisper_compute(_cls, value: str) -> str:
        if value not in WHISPER_COMPUTE_TYPES:
            allowed = ", ".join(sorted(WHISPER_COMPUTE_TYPES))
            raise ValueError(f"whisper_compute_type must be one of: {allowed}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return LocalSentenceTransformerAdapter(settings.embedding_model)


@lru_cache
def get_vector_store() -> QdrantAdapter:
    settings = get_settings()
    embedder = get_embedding_provider()
    return QdrantAdapter(
        url=settings.qdrant_url,
        collection=settings.qdrant_collection,
        vector_size=embedder.dimension,
    )


def build_llm_provider(settings: Settings | None = None) -> LLMProvider:
    cfg = settings or get_settings()
    provider = cfg.llm_provider.lower()
    if provider == "openai":
        if not cfg.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIAdapter(cfg.openai_api_key, cfg.openai_model)
    if provider == "anthropic":
        if not cfg.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicAdapter(cfg.anthropic_api_key, cfg.anthropic_model)
    return OllamaAdapter(cfg.ollama_base_url, cfg.ollama_model)


def get_vector_store_typed() -> VectorStore:
    return get_vector_store()


@lru_cache
def get_transcription_provider() -> TranscriptionProvider:
    settings = get_settings()
    return FasterWhisperAdapter(
        model_size=settings.whisper_model_size,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )


def build_transcription_provider(settings: Settings | None = None) -> TranscriptionProvider:
    cfg = settings or get_settings()
    return FasterWhisperAdapter(
        model_size=cfg.whisper_model_size,
        device=cfg.whisper_device,
        compute_type=cfg.whisper_compute_type,
    )
