"""Vector store manager for Qdrant integration with Ollama embeddings.

This module manages the lifecycle of the Qdrant vector store and handles
bootstrapping of schema documents on application startup.
"""

import logging
from typing import Optional

from langchain_ollama import OllamaEmbeddings
try:
    from langchain_qdrant import QdrantVectorStore
except ImportError:
    from langchain_qdrant import Qdrant as QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.config.settings import settings
from app.core.router_seed import seed_qdrant, get_schema_documents

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages Qdrant vector store and embeddings lifecycle."""

    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.embeddings: Optional[OllamaEmbeddings] = None
        self.vector_store: Optional[QdrantVectorStore] = None
        self._initialized = False

    async def bootstrap(self) -> None:
        """Initialize Qdrant and Ollama embeddings, seed schema documents."""
        if self._initialized:
            logger.info("VectorStoreManager already initialized")
            return

        try:
            logger.info("Initializing VectorStoreManager...")

            # Initialize Qdrant client
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                timeout=10.0,
            )
            logger.info("Connected to Qdrant at %s", settings.QDRANT_URL)

            # Initialize Ollama embeddings
            self.embeddings = OllamaEmbeddings(
                model=settings.EMBEDDING_MODEL,
            )
            logger.info("Initialized Ollama embeddings with model: %s", settings.EMBEDDING_MODEL)

            # Check if collection exists; create if missing
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if settings.QDRANT_COLLECTION not in collection_names:
                logger.info(
                    "Creating Qdrant collection '%s' with Cosine distance...",
                    settings.QDRANT_COLLECTION,
                )
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=768,  # Match embedding dimension
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Collection created: %s", settings.QDRANT_COLLECTION)
            else:
                logger.info("Collection already exists: %s", settings.QDRANT_COLLECTION)

            # Initialize LangChain vector store
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=settings.QDRANT_COLLECTION,
                embeddings=self.embeddings,
            )
            logger.info("LangChain QdrantVectorStore initialized")

            # Seed schema documents if collection is empty
            try:
                collection_info = self.client.get_collection(settings.QDRANT_COLLECTION)
                if collection_info.points_count == 0:
                    logger.info("Seeding schema documents into Qdrant...")
                    await seed_qdrant(self.vector_store)
                    logger.info("Schema documents seeded successfully")
                else:
                    logger.info(
                        "Qdrant collection already has %d documents",
                        collection_info.points_count,
                    )
            except Exception as e:
                logger.warning("Failed to seed schema documents: %s", e)

            self._initialized = True
            logger.info("VectorStoreManager bootstrap complete")

        except Exception as e:
            logger.error("Failed to bootstrap VectorStoreManager: %s", e)
            raise

    async def close(self) -> None:
        """Clean up resources."""
        try:
            if self.client:
                self.client.close()
                logger.info("Qdrant client closed")
        except Exception as e:
            logger.error("Error closing Qdrant client: %s", e)

    def get_vector_store(self) -> QdrantVectorStore:
        """Return initialized vector store."""
        if not self._initialized or self.vector_store is None:
            raise RuntimeError(
                "VectorStoreManager not initialized; call bootstrap() first"
            )
        return self.vector_store

    def get_embeddings(self) -> OllamaEmbeddings:
        """Return initialized embeddings model."""
        if not self._initialized or self.embeddings is None:
            raise RuntimeError(
                "VectorStoreManager not initialized; call bootstrap() first"
            )
        return self.embeddings


# Global instance
_manager: Optional[VectorStoreManager] = None


def get_vector_manager() -> VectorStoreManager:
    """Get or create the global vector store manager."""
    global _manager
    if _manager is None:
        _manager = VectorStoreManager()
    return _manager
