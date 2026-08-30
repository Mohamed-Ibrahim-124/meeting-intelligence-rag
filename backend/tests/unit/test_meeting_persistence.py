from pathlib import Path

from clinical_meeting.adapters.storage.meeting_registry import JsonMeetingRegistry
from clinical_meeting.services.ingestion import IngestionService
from tests.support.fakes import FakeEmbedder
from tests.support.memory_store import InMemoryVectorStore

TRANSCRIPT = """
[00:01:03] Dr. Chen: We decided to require hemoglobin above 11 g/dL for enrollment.
[00:01:45] Nurse Patel: Action item — update the consent form by Friday.
"""


def test_registry_survives_new_service_instance(tmp_path: Path) -> None:
    registry = JsonMeetingRegistry(tmp_path / "meetings.json")
    store = InMemoryVectorStore()
    first = IngestionService(FakeEmbedder(), store, registry=registry)
    meta = first.ingest("Trial", TRANSCRIPT, meeting_id="persist-1")
    assert meta.meeting_id == "persist-1"

    second = IngestionService(FakeEmbedder(), store, registry=registry)
    restored = second.get_metadata("persist-1")
    assert restored is not None
    assert restored.title == "Trial"
    assert restored.participants
    assert second.get_turns("persist-1")


def test_restore_from_vector_store_when_registry_missing(tmp_path: Path) -> None:
    store = InMemoryVectorStore()
    first = IngestionService(
        FakeEmbedder(), store, registry=JsonMeetingRegistry(tmp_path / "a.json")
    )
    first.ingest("Trial", TRANSCRIPT, meeting_id="orphan-1")

    second = IngestionService(
        FakeEmbedder(), store, registry=JsonMeetingRegistry(tmp_path / "b.json")
    )
    restored = second.get_metadata("orphan-1")
    assert restored is not None
    assert restored.chunk_count >= 1
    assert restored.turn_count >= 1
    assert second.get_turns("orphan-1")
