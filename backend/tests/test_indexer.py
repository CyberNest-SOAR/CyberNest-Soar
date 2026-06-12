import asyncio
from types import SimpleNamespace

from app.services.indexer import get_indexer
from app.schemas.models import UnifiedAlert, HostContext


class FakeVectorStore:
    def __init__(self):
        self.added = []

    def add_documents(self, docs, ids=None):
        self.added.append((docs, ids))


class FakeManager:
    def __init__(self, vs):
        self.vector_store = vs
        self._initialized = True

    def get_vector_store(self):
        return self.vector_store


def test_indexer_adds_document(monkeypatch):
    fake_vs = FakeVectorStore()
    fake_mgr = FakeManager(fake_vs)

    # Monkeypatch get_vector_manager to return our fake manager
    monkeypatch.setattr("app.services.vector_manager.get_vector_manager", lambda: fake_mgr)

    indexer = get_indexer()

    alert = UnifiedAlert(
        event_id="evt-1",
        source="wazuh",
        timestamp="2024-01-01T00:00:00Z",
        description="Test alert",
        severity=5,
        host_context=HostContext(hostname="host1", ip_address="10.0.0.1"),
        raw_data={"foo": "bar"},
    )

    # Run the indexing coroutine
    asyncio.get_event_loop().run_until_complete(indexer._index_alert(alert))

    assert len(fake_vs.added) == 1
    docs, ids = fake_vs.added[0]
    assert ids[0] == "alert::evt-1"
    assert "Test alert" in docs[0].page_content
