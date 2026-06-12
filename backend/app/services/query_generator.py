"""Semantic query generation engine using LangChain Expression Language (LCEL).

This module implements the core semantic routing logic. It uses vector similarity
search to match user queries to database schemas, then generates precise SQL or
OpenSearch DSL queries using a local LLM.
"""

import logging
import json
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from langchain_ollama import ChatOllama

from app.config.settings import settings
from app.schemas.rag_models import RoutedQueryPayload
from app.services.vector_manager import get_vector_manager

logger = logging.getLogger(__name__)


class QueryGenerationEngine:
    """Semantic routing and query generation using LLM + vector retrieval."""

    def __init__(self):
        self.llm = ChatOllama(
            model=settings.ROUTING_LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.0,  # Deterministic for query generation
            num_ctx=4096,
        )
        self.vector_manager = get_vector_manager()
        self._chain = None
        logger.info("QueryGenerationEngine initialized with model: %s", settings.ROUTING_LLM_MODEL)

    async def initialize(self) -> None:
        """Initialize the LCEL chain after vector manager is ready."""
        if self._chain is not None:
            return

        # Build the LCEL chain
        prompt = ChatPromptTemplate.from_template(
            """You are a semantic query generator. You have been given context about available databases.

Available Database Schemas:
{context}

User Query: {user_query}

Your task is to:
1. Identify which database(s) the user is asking about based on the context above.
2. Generate the precise query (SQL for PostgreSQL, JSON DSL for OpenSearch) that answers the question.
3. Explain your reasoning briefly.

Return a JSON object with the following structure:
{{
  "target_db": "postgresql" or "opensearch",
  "target_source": "table or index name",
  "executable_query": "the actual query string",
  "reasoning": "brief explanation"
}}

Important rules:
- If the query requires both databases, prioritize the one that best answers the user's question.
- For PostgreSQL queries, use standard SQL with proper syntax.
- For OpenSearch queries, return valid JSON DSL format.
- Do NOT return incomplete or pseudo-code queries.
- Always explain why you chose this database and query approach.

JSON Response:"""
        )

        parser = JsonOutputParser(pydantic_object=RoutedQueryPayload)

        # LCEL chain: prompt -> llm -> parser
        self._chain = prompt | self.llm | parser

        logger.info("QueryGenerationEngine LCEL chain initialized")

    async def generate_query(self, user_query: str) -> RoutedQueryPayload:
        """
        Generate a routed database query from a natural language question.

        Args:
            user_query: Natural language question from the user

        Returns:
            RoutedQueryPayload with target_db, target_source, executable_query, and reasoning
        """
        if self._chain is None:
            await self.initialize()

        try:
            # Retrieve schema context from Qdrant
            vector_store = self.vector_manager.get_vector_store()
            schema_docs: list[Document] = vector_store.similarity_search(
                user_query,
                k=2,  # Get top 2 most relevant schema docs
            )

            context = "\n\n".join([
                f"Database: {doc.metadata.get('target_db', 'unknown')}\n"
                f"Description: {doc.page_content}\n"
                f"Tables/Indices: {json.dumps(doc.metadata.get('tables', doc.metadata.get('indices', [])), indent=2)}"
                for doc in schema_docs
            ])

            logger.debug("Retrieved schema context for query generation")

            # Invoke the LCEL chain
            result = await self._chain.ainvoke({
                "context": context,
                "user_query": user_query,
            })

            logger.info(
                "Generated query targeting %s.%s",
                result.target_db,
                result.target_source,
            )

            return result

        except Exception as e:
            logger.error("Failed to generate query: %s", e)
            raise

    async def close(self) -> None:
        """Clean up resources."""
        # ChatOllama doesn't require explicit cleanup
        pass


# Global instance
_engine: Optional[QueryGenerationEngine] = None


def get_query_engine() -> QueryGenerationEngine:
    """Get or create the global query generation engine."""
    global _engine
    if _engine is None:
        _engine = QueryGenerationEngine()
    return _engine
