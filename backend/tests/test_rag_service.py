import asyncio

from types import SimpleNamespace

import pytest

from app.services.rag_service import RAGService
from app.schemas.rag_models import RoutedQueryPayload


class FakeEngine:
    def __init__(self, payload):
        self._payload = payload

    async def generate_query(self, user_query):
        return self._payload


@pytest.mark.asyncio
async def test_rag_service_process_query_postgres(monkeypatch):
    payload = RoutedQueryPayload(
        target_db="postgresql",
        target_source="incidents",
        executable_query="SELECT id, description FROM incidents",
        reasoning="matched incidents schema",
    )

    # Stub out query generator
    monkeypatch.setattr("app.services.query_generator.get_query_engine", lambda: FakeEngine(payload))

    # Stub out executor to return fake rows
    async def fake_exec(query, limit=10):
        return [{"id": 1, "description": "incident"}]

    monkeypatch.setattr("app.services.rag_service.QueryExecutionService.execute_postgresql_query", fake_exec)

    rag = RAGService()
    resp = await rag.process_query("show incidents", limit=5)

    assert resp.routed_query.target_db == "postgresql"
    assert isinstance(resp.raw_results, list)
    assert "formatted_answer" in resp.__fields__ or hasattr(resp, "formatted_answer")


@pytest.mark.asyncio
async def test_rag_service_process_query_opensearch(monkeypatch):
    payload = RoutedQueryPayload(
        target_db="opensearch",
        target_source="suricata-logs-*",
        executable_query='{"query": {"match_all": {}}}',
        reasoning="matched network schema",
    )

    monkeypatch.setattr("app.services.query_generator.get_query_engine", lambda: FakeEngine(payload))

    async def fake_os(query, limit=10):
        return [{"msg": "doc1"}, {"msg": "doc2"}]

    monkeypatch.setattr("app.services.rag_service.QueryExecutionService.execute_opensearch_query", fake_os)

    rag = RAGService()
    resp = await rag.process_query("network activity", limit=2)

    assert resp.routed_query.target_db == "opensearch"
    assert len(resp.raw_results) == 2
