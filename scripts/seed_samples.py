#!/usr/bin/env python3
"""Seed sample transcripts into a running API."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples" / "transcripts"
API = "http://localhost:8000"


def main() -> None:
    api = sys.argv[1] if len(sys.argv) > 1 else API
    for path in sorted(SAMPLES.glob("*.txt")):
        title = path.stem.replace("_", " ").title()
        with path.open("rb") as handle:
            response = httpx.post(
                f"{api}/api/v1/meetings",
                data={"title": title},
                files={"file": (path.name, handle, "text/plain")},
                timeout=120.0,
            )
        response.raise_for_status()
        print(f"Seeded {title}: {response.json()['meeting_id']}")


if __name__ == "__main__":
    main()
