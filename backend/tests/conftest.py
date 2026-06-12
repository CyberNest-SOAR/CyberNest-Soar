import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Prevent tests from making real network calls unless explicitly allowed."""
    async def fake_start(self=None):
        return None

    # Stub out vector manager bootstrap to avoid real Qdrant/Ollama connections during tests
    monkeypatch.setattr("app.services.vector_manager.VectorStoreManager.bootstrap", fake_start, raising=False)
    yield
