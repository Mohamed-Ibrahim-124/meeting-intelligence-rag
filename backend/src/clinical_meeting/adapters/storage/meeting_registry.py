from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from clinical_meeting.domain.models import MeetingMetadata, TranscriptTurn


class JsonMeetingRegistry:
    """Persist meeting metadata and turns so API restarts keep the UI usable."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._data = {}
            return
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        self._data = raw if isinstance(raw, dict) else {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def save_meeting(
        self,
        metadata: MeetingMetadata,
        turns: list[TranscriptTurn],
        title: str | None = None,
    ) -> None:
        self._data[metadata.meeting_id] = {
            "meeting_id": metadata.meeting_id,
            "title": title or metadata.title,
            "uploaded_at": metadata.uploaded_at.isoformat(),
            "turn_count": metadata.turn_count,
            "chunk_count": metadata.chunk_count,
            "participants": metadata.participants,
            "turns": [
                {
                    "timestamp": t.timestamp,
                    "speaker": t.speaker,
                    "text": t.text,
                    "turn_index": t.turn_index,
                }
                for t in turns
            ],
        }
        self._save()

    def get_metadata(self, meeting_id: str) -> MeetingMetadata | None:
        row = self._data.get(meeting_id)
        if not row:
            return None
        return MeetingMetadata(
            meeting_id=meeting_id,
            title=str(row.get("title", meeting_id)),
            uploaded_at=datetime.fromisoformat(str(row["uploaded_at"])),
            turn_count=int(row.get("turn_count", 0)),
            chunk_count=int(row.get("chunk_count", 0)),
            participants=list(row.get("participants", [])),
        )

    def get_turns(self, meeting_id: str) -> list[TranscriptTurn]:
        row = self._data.get(meeting_id)
        if not row:
            return []
        turns: list[TranscriptTurn] = []
        for item in row.get("turns", []):
            turns.append(
                TranscriptTurn(
                    meeting_id=meeting_id,
                    timestamp=str(item["timestamp"]),
                    speaker=str(item["speaker"]),
                    text=str(item["text"]),
                    turn_index=int(item["turn_index"]),
                )
            )
        return turns

    def list_metadata(self) -> list[MeetingMetadata]:
        result: list[MeetingMetadata] = []
        for meeting_id in sorted(self._data.keys()):
            meta = self.get_metadata(meeting_id)
            if meta:
                result.append(meta)
        return result

    def delete(self, meeting_id: str) -> None:
        if meeting_id in self._data:
            del self._data[meeting_id]
            self._save()
