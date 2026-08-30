"""Optional RAG evaluation — run locally when LLM credentials are configured."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ragas_available() -> bool:
    return importlib.util.find_spec("ragas") is not None


async def run_deterministic_eval() -> dict:
    from clinical_meeting.adapters.vector.qdrant_adapter import QdrantAdapter
    from clinical_meeting.config import (
        build_llm_provider,
        get_embedding_provider,
        get_settings,
    )
    from clinical_meeting.services.answer import AnswerService
    from clinical_meeting.services.ingestion import IngestionService
    from clinical_meeting.services.retrieval import RetrievalService

    golden = json.loads((ROOT / "eval" / "golden_qa.json").read_text(encoding="utf-8"))
    transcript = (ROOT / golden["transcript_file"]).read_text(encoding="utf-8")
    settings = get_settings()
    embedder = get_embedding_provider()
    store = QdrantAdapter(settings.qdrant_url, settings.qdrant_collection, embedder.dimension)
    ingestion = IngestionService(embedder, store, settings.max_upload_bytes)
    meeting_id = golden["meeting_id"]
    ingestion.ingest("Golden Eval", transcript, meeting_id=meeting_id)
    retrieval = RetrievalService(embedder, store, settings.retrieval_top_k, settings.max_context_tokens)
    llm = build_llm_provider(settings)
    answer = AnswerService(llm, retrieval)

    results = []
    for item in golden["questions"]:
        result = await answer.answer(meeting_id, item["question"])
        passed = True
        if item.get("answerable", True):
            passed = not result.refused and bool(result.citations)
            if item.get("expected_speaker"):
                passed = passed and any(c.speaker == item["expected_speaker"] for c in result.citations)
        else:
            passed = result.refused or "insufficient" in result.answer.lower()
        results.append({"id": item["id"], "passed": passed, "refused": result.refused})
    return {"total": len(results), "passed": sum(r["passed"] for r in results), "results": results}


def main() -> None:
    if os.getenv("SKIP_RAGAS", "1") == "1":
        summary = asyncio.run(run_deterministic_eval())
        print(json.dumps(summary, indent=2))
        return
    if not _ragas_available():
        print("RAGAs not installed. Run deterministic eval only.")
        summary = asyncio.run(run_deterministic_eval())
        print(json.dumps(summary, indent=2))
        return
    summary = asyncio.run(run_deterministic_eval())
    print("Deterministic eval:", json.dumps(summary, indent=2))
    print("RAGAs available — extend run_eval.py with Dataset rows for full LLM-judged metrics.")


if __name__ == "__main__":
    main()
