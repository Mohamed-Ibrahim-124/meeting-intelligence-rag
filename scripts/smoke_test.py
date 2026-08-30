#!/usr/bin/env python3
"""End-to-end smoke test against a running API."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
API = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
TIMEOUT = 300.0


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        raise SystemExit(1)


def main() -> None:
    client = httpx.Client(base_url=API, timeout=TIMEOUT)
    print(f"Smoke test -> {API}\n")

    r = client.get("/health")
    check("health", r.status_code == 200, r.text)

    sample = ROOT / "samples" / "transcripts" / "trial_protocol_review.txt"
    with sample.open("rb") as f:
        r = client.post(
            "/api/v1/meetings",
            data={"title": "Smoke Test Meeting"},
            files={"file": ("trial.txt", f, "text/plain")},
        )
    check("text upload", r.status_code == 200, r.text[:120])
    meeting_id = r.json()["meeting_id"]

    r = client.get("/api/v1/meetings")
    check("list meetings", r.status_code == 200 and any(m["meeting_id"] == meeting_id for m in r.json()))

    r = client.get(f"/api/v1/meetings/{meeting_id}")
    check("meeting detail", r.status_code == 200 and len(r.json()["turns"]) > 0)

    r = client.post(
        f"/api/v1/meetings/{meeting_id}/query",
        json={"question": "What enrollment target was discussed?"},
    )
    check("RAG query", r.status_code == 200 and bool(r.json().get("answer")), r.text[:120])

    audio = ROOT / "samples" / "audio" / "jfk.wav"
    with audio.open("rb") as f:
        r = client.post(
            "/api/v1/meetings/from-audio",
            data={"title": "Smoke Audio", "default_speaker": "Speaker"},
            files={"file": ("jfk.wav", f, "audio/wav")},
        )
    check("audio upload", r.status_code == 200, r.text[:120])
    audio_id = r.json()["meeting_id"]

    r = client.get(f"/api/v1/meetings/{audio_id}/summary")
    check("summary endpoint", r.status_code == 200 or r.status_code == 404, str(r.status_code))

    r = client.get(f"/api/v1/meetings/{meeting_id}/decisions")
    check("decisions endpoint", r.status_code == 200, f"{len(r.json())} decisions")

    print("\nAll smoke checks passed.")
    print(json.dumps({"text_meeting_id": meeting_id, "audio_meeting_id": audio_id}, indent=2))


if __name__ == "__main__":
    main()
