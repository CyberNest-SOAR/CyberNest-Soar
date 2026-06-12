"""Indexer service: upsert normalized alerts/documents into Qdrant for routing.

This service exposes async helper methods that run the synchronous
LangChain vector store indexing in a threadpool to avoid blocking the
event loop. Documents are represented as LangChain `Document` objects
with metadata useful for retrieval and debugging.
"""

import asyncio
import json
import logging
from typing import Optional

from langchain_core.documents import Document

from app.services.vector_manager import get_vector_manager
from app.schemas.models import UnifiedAlert

logger = logging.getLogger(__name__)


class Indexer:
    def __init__(self):
        self.vector_manager = get_vector_manager()

    async def index_alert_async(self, alert: UnifiedAlert) -> None:
        """Schedule an alert for indexing (non-blocking).

        This creates a background task that runs the blocking add_documents
        call inside a thread using `asyncio.to_thread`.
        """
        try:
            asyncio.create_task(self._index_alert(alert))
        except Exception as e:
            logger.warning("Failed to schedule index task for %s: %s", alert.event_id, e)

    async def _index_alert(self, alert: UnifiedAlert) -> None:
        """Index a single alert into the Qdrant vector store."""
        try:
            vector_store = self.vector_manager.get_vector_store()

            # Build a compact textual representation for embedding
            doc_text = (
                f"{alert.description}\n\n" + json.dumps(alert.raw_data, default=str))

            doc = Document(
                page_content=doc_text,
                metadata={
                    "event_id": alert.event_id,
                    "source": alert.source,
                    "timestamp": str(alert.timestamp),
                    "ip": alert.host_context.ip_address,
                    "target_db": "opensearch",
                },
            )

            # Blocking call executed in threadpool to avoid blocking event loop
            await asyncio.to_thread(
                lambda: vector_store.add_documents([doc], ids=[f"alert::{alert.event_id}"])
            )

            logger.debug("Indexed alert %s into Qdrant", alert.event_id)

        except Exception as e:
            logger.warning("Indexing alert %s failed: %s", getattr(alert, "event_id", "unknown"), e)


# Singleton
_indexer: Optional[Indexer] = None


def get_indexer() -> Indexer:
    global _indexer
    if _indexer is None:
        _indexer = Indexer()
    return _indexer
