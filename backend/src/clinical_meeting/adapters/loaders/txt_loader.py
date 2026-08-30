import re
from pathlib import Path

from clinical_meeting.domain.models import TranscriptTurn

LINE_PATTERN = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s+([^:]+):\s*(.+)$")


class TranscriptParser:
    def parse(self, meeting_id: str, content: str) -> list[TranscriptTurn]:
        turns: list[TranscriptTurn] = []
        for index, raw_line in enumerate(content.splitlines()):
            line = raw_line.strip()
            if not line:
                continue
            match = LINE_PATTERN.match(line)
            if not match:
                msg = f"Invalid transcript line at {index + 1}: {line[:80]}"
                raise ValueError(msg)
            timestamp, speaker, text = match.groups()
            turns.append(
                TranscriptTurn(
                    meeting_id=meeting_id,
                    timestamp=timestamp,
                    speaker=speaker.strip(),
                    text=text.strip(),
                    turn_index=len(turns),
                )
            )
        if not turns:
            raise ValueError("Transcript contains no valid turns")
        return turns


class TxtTranscriptLoader:
    def load(self, meeting_id: str, path: Path) -> list[TranscriptTurn]:
        content = path.read_text(encoding="utf-8")
        return TranscriptParser().parse(meeting_id, content)

    def load_text(self, meeting_id: str, content: str) -> list[TranscriptTurn]:
        return TranscriptParser().parse(meeting_id, content)
