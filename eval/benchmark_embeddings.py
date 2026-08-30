"""Benchmark two embedding models on golden retrieval questions."""

from __future__ import annotations

import json
import time
from pathlib import Path

from clinical_meeting.adapters.chunking.speaker_turn_chunker import SpeakerTurnChunker
from clinical_meeting.adapters.embeddings.local_st import LocalSentenceTransformerAdapter
from clinical_meeting.adapters.loaders.txt_loader import TxtTranscriptLoader
from clinical_meeting.services.retrieval import RetrievalService
from clinical_meeting.adapters.vector.qdrant_adapter import QdrantAdapter

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "eval" / "golden_qa.json"
OUTPUT = ROOT / "eval" / "embedding_benchmark.json"

CANDIDATES = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
]


def _recall_at_k(expected_speaker: str | None, citations_speakers: list[str], k: int = 5) -> float:
    if not expected_speaker:
        return 1.0
    top = citations_speakers[:k]
    return 1.0 if expected_speaker in top else 0.0


def benchmark_model(model_name: str, meeting_id: str, transcript: str, questions: list[dict]) -> dict:
    embedder = LocalSentenceTransformerAdapter(model_name)
    store = QdrantAdapter("http://localhost:6333", f"bench_{model_name.replace('/', '_')}", embedder.dimension)
    loader = TxtTranscriptLoader()
    chunker = SpeakerTurnChunker()
    turns = loader.load_text(meeting_id, transcript)
    chunks = chunker.chunk(turns)
    vectors = embedder.embed([c.text for c in chunks])
    store.delete_meeting(meeting_id)
    store.upsert_chunks(meeting_id, chunks, vectors)
    retrieval = RetrievalService(embedder, store, top_k=5)

    scores: list[float] = []
    latencies: list[float] = []
    for item in questions:
        if not item.get("answerable", True):
            continue
        start = time.perf_counter()
        results = retrieval.retrieve(meeting_id, item["question"])
        latencies.append((time.perf_counter() - start) * 1000)
        speakers = [r.chunk.speaker for r in results]
        scores.append(_recall_at_k(item.get("expected_speaker"), speakers))
    recall = sum(scores) / len(scores) if scores else 0.0
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
    return {
        "model": model_name,
        "recall_at_5": round(recall, 3),
        "mean_latency_ms": round(mean_latency, 1),
        "memory_mb_approx": 130 if "bge" in model_name else 90,
    }


def main() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    transcript_path = ROOT / golden["transcript_file"]
    transcript = transcript_path.read_text(encoding="utf-8")
    meeting_id = golden["meeting_id"]
    questions = golden["questions"]

    results = [benchmark_model(model, meeting_id, transcript, questions) for model in CANDIDATES]
    best = max(results, key=lambda r: (r["recall_at_5"], -r["mean_latency_ms"]))
    for row in results:
        row["selected"] = row["model"] == best["model"]
    payload = {
        "benchmark_date": time.strftime("%Y-%m-%d"),
        "dataset": str(GOLDEN.relative_to(ROOT)),
        "metric": "Recall@5 + mean embed/retrieve latency ms",
        "candidates": results,
        "decision": f"Selected {best['model']} based on retrieval recall and latency.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
