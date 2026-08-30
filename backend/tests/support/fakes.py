from clinical_meeting.domain.models import LLMResponse, TranscriptSegment


class FakeLLM:
    def __init__(self, text: str = "Dr. Chen discussed enrollment criteria at 00:01:23.") -> None:
        self._text = text

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(text=self._text, token_usage=10)

    @property
    def provider_name(self) -> str:
        return "fake"

    @property
    def model_name(self) -> str:
        return "fake-model"


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0, 0.5] for text in texts]

    @property
    def dimension(self) -> int:
        return 3


class FakeTranscriptionProvider:
    def __init__(
        self,
        segments: list[TranscriptSegment] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self._segments = (
            segments
            if segments is not None
            else [
                TranscriptSegment(0.0, 2.5, "We will enroll twenty patients."),
                TranscriptSegment(2.5, 5.0, "Please update the protocol."),
            ]
        )
        self._fail = fail
        self.calls: list[str] = []

    @property
    def model_name(self) -> str:
        return "fake-whisper"

    def transcribe(self, audio_path: object) -> list[TranscriptSegment]:
        self.calls.append(str(audio_path))
        if self._fail:
            raise RuntimeError("model load failed")
        return list(self._segments)
