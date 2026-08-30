"""Shared application constants — no magic numbers in services/adapters."""

from __future__ import annotations

# Text transcript upload
ALLOWED_TEXT_SUFFIXES: frozenset[str] = frozenset({".txt"})
DEFAULT_MAX_TEXT_UPLOAD_BYTES: int = 1_048_576

# Audio upload / transcription
ALLOWED_AUDIO_SUFFIXES: frozenset[str] = frozenset({".wav", ".mp3", ".m4a", ".webm", ".ogg"})
ALLOWED_AUDIO_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/webm",
        "audio/ogg",
        "application/octet-stream",
    }
)
DEFAULT_MAX_AUDIO_UPLOAD_BYTES: int = 50 * 1024 * 1024
DEFAULT_TRANSCRIPT_SPEAKER: str = "Speaker"

# faster-whisper model sizes (Hugging Face Systran/faster-whisper-*)
WHISPER_MODEL_SIZES: frozenset[str] = frozenset(
    {
        "tiny",
        "base",
        "small",
        "medium",
        "large-v3",
        "large-v3-turbo",
    }
)
DEFAULT_WHISPER_MODEL_SIZE: str = "small"
WHISPER_DEVICES: frozenset[str] = frozenset({"auto", "cpu", "cuda"})
DEFAULT_WHISPER_DEVICE: str = "auto"
WHISPER_COMPUTE_TYPES: frozenset[str] = frozenset(
    {"default", "int8", "float16", "int8_float16", "float32"}
)
DEFAULT_WHISPER_COMPUTE_TYPE: str = "default"

# Timestamp formatting
SECONDS_PER_MINUTE: int = 60
SECONDS_PER_HOUR: int = 3600

# Chunking (existing pipeline defaults, centralized for new/touched code)
MERGE_TOKEN_LIMIT: int = 50
MAX_CHUNK_TOKENS: int = 400
APPROX_CHARS_PER_TOKEN: int = 4
