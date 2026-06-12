import asyncio
from types import SimpleNamespace

from langchain_core.documents import Document

from app.services.query_generator import get_query_engine
from app.schemas.rag_models import RoutedQueryPayload


class StubChain:
    def __init__(self, response):
        self._response = response

    async def ainvoke(self, inputs):
        return self._response


class FakeVectorStore:
    def similarity_search(self, query, k=2):
        return [Document(page_content="schema", metadata={"target_db": "postgresql", "tables": []})]


def test_generate_query_uses_vector_store_and_chain(monkeypatch):
    engine = get_query_engine()

    # Patch vector manager to return fake vector store
    monkeypatch.setattr("app.services.vector_manager.get_vector_manager", lambda: SimpleNamespace(get_vector_store=lambda: FakeVectorStore()))

    # Provide a stubbed chain response
    payload = RoutedQueryPayload(
        target_db="postgresql",
        target_source="incidents",
        executable_query="SELECT 1",
        reasoning="test",
    )

    engine._chain = StubChain(payload)

    result = asyncio.get_event_loop().run_until_complete(engine.generate_query("test query"))
    assert result.target_db == "postgresql"
    assert result.executable_query == "SELECT 1"
