import re

from clinical_meeting.constants import (
    APPROX_CHARS_PER_TOKEN,
    MAX_CHUNK_TOKENS,
    MERGE_TOKEN_LIMIT,
)
from clinical_meeting.domain.models import Chunk, TranscriptTurn

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // APPROX_CHARS_PER_TOKEN)


class SpeakerTurnChunker:
    def chunk(self, turns: list[TranscriptTurn]) -> list[Chunk]:
        if not turns:
            return []
        groups = self._merge_short_turns(turns)
        raw_groups: list[list[TranscriptTurn]] = []
        for group in groups:
            text = " ".join(t.text for t in group)
            if _approx_tokens(text) <= MAX_CHUNK_TOKENS:
                raw_groups.append(group)
            else:
                for turn in group:
                    raw_groups.extend([[part] for part in self._split_long_turn(turn)])

        chunks: list[Chunk] = []
        meeting_id = turns[0].meeting_id
        for index, group in enumerate(raw_groups):
            text = " ".join(t.text for t in group)
            speakers = {t.speaker for t in group}
            speaker = group[0].speaker if len(speakers) == 1 else "Multiple"
            chunks.append(
                Chunk(
                    chunk_id=f"{meeting_id}-chunk-{index}",
                    meeting_id=meeting_id,
                    text=text,
                    speaker=speaker,
                    start_time=group[0].timestamp,
                    end_time=group[-1].timestamp,
                    chunk_index=index,
                    turn_index_start=group[0].turn_index,
                    turn_index_end=group[-1].turn_index,
                )
            )
        return chunks

    def _merge_short_turns(self, turns: list[TranscriptTurn]) -> list[list[TranscriptTurn]]:
        groups: list[list[TranscriptTurn]] = []
        buffer: list[TranscriptTurn] = []

        def flush() -> None:
            nonlocal buffer
            if buffer:
                groups.append(buffer)
                buffer = []

        for turn in turns:
            if buffer and buffer[-1].speaker == turn.speaker:
                combined = " ".join(t.text for t in buffer) + " " + turn.text
                if _approx_tokens(combined) <= MERGE_TOKEN_LIMIT:
                    buffer.append(turn)
                    continue
                flush()
            elif buffer:
                flush()
            buffer = [turn]
        flush()
        return groups

    def _split_long_turn(self, turn: TranscriptTurn) -> list[TranscriptTurn]:
        sentences = SENTENCE_SPLIT.split(turn.text)
        parts: list[TranscriptTurn] = []
        current = ""
        part_index = 0
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip()
            if current and _approx_tokens(candidate) > MAX_CHUNK_TOKENS:
                parts.append(
                    TranscriptTurn(
                        meeting_id=turn.meeting_id,
                        timestamp=turn.timestamp,
                        speaker=turn.speaker,
                        text=current.strip(),
                        turn_index=turn.turn_index * 100 + part_index,
                    )
                )
                part_index += 1
                current = sentence
            else:
                current = candidate
        if current.strip():
            parts.append(
                TranscriptTurn(
                    meeting_id=turn.meeting_id,
                    timestamp=turn.timestamp,
                    speaker=turn.speaker,
                    text=current.strip(),
                    turn_index=turn.turn_index * 100 + part_index,
                )
            )
        return parts
