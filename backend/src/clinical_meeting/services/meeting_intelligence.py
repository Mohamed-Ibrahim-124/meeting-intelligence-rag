from clinical_meeting.domain.models import ActionItem, Decision, Topic
from clinical_meeting.ports import LLMProvider
from clinical_meeting.services.guardrails import (
    extract_action_items,
    extract_decisions,
    extract_topics,
)
from clinical_meeting.services.ingestion import IngestionService
from clinical_meeting.services.retrieval import RetrievalService

SUMMARY_SYSTEM = (
    "Summarize the clinical meeting using only the provided transcript excerpts. "
    "Keep it concise (3-5 sentences). Mention key participants and outcomes."
)


class MeetingIntelligenceService:
    def __init__(
        self,
        llm: LLMProvider,
        retrieval_service: RetrievalService,
        ingestion_service: IngestionService,
    ) -> None:
        self._llm = llm
        self._retrieval = retrieval_service
        self._ingestion = ingestion_service

    def get_participants(self, meeting_id: str) -> list[str]:
        meta = self._ingestion.get_metadata(meeting_id)
        if meta and meta.participants:
            return meta.participants
        turns = self._ingestion.get_turns(meeting_id)
        return sorted({t.speaker for t in turns})

    def get_action_items(self, meeting_id: str) -> list[ActionItem]:
        turns = self._ingestion.get_turns(meeting_id)
        return extract_action_items(turns)

    def get_decisions(self, meeting_id: str) -> list[Decision]:
        turns = self._ingestion.get_turns(meeting_id)
        return extract_decisions(turns)

    def get_topics(self, meeting_id: str) -> list[Topic]:
        turns = self._ingestion.get_turns(meeting_id)
        return extract_topics(turns)

    async def get_summary(self, meeting_id: str) -> str:
        chunks = self._retrieval.retrieve(meeting_id, "meeting summary decisions action items")
        if not chunks:
            return "No transcript content available for summary."
        context = self._retrieval.build_context(chunks)
        participants = ", ".join(self.get_participants(meeting_id))
        user_prompt = f"Participants: {participants}\n\nTranscript excerpts:\n{context}"
        response = await self._llm.complete(SUMMARY_SYSTEM, user_prompt)
        return response.text.strip()
