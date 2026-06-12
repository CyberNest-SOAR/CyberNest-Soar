"""RAG service layer for semantic query routing, execution, and synthesis."""

import json
import logging
from typing import Any, Optional
from urllib.parse import urlparse

from opensearchpy import AsyncOpenSearch

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.schemas.rag_models import RoutedQueryPayload, RAGQueryResponse
from app.services.query_generator import get_query_engine

logger = logging.getLogger(__name__)


class QueryExecutionService:
    """Service for executing routed queries against target databases."""

    @staticmethod
    async def execute_postgresql_query(
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute a SQL query against PostgreSQL.

        Args:
            query: SQL query string
            limit: Maximum rows to return (appended if not in query)

        Returns:
            List of result dictionaries
        """
        try:
            # Create async engine for PostgreSQL
            engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                future=True,
            )

            async with engine.begin() as conn:
                # Append LIMIT if not already present
                if "LIMIT" not in query.upper():
                    query = f"{query} LIMIT {limit}"

                result = await conn.execute(text(query))
                rows = await result.fetchall()

                # Convert Row objects to dicts
                results = [dict(row._mapping) for row in rows]
                logger.info("PostgreSQL query returned %d rows", len(results))
                return results

        except Exception as e:
            logger.error("PostgreSQL query execution failed: %s", e)
            raise

    @staticmethod
    async def execute_opensearch_query(
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Execute a query against OpenSearch using `opensearch-py`.

        Accepts either a JSON string representing the full search body
        (optionally including an `index` field) or a plain JSON body.
        """
        try:
            # Parse executable_query which should be JSON DSL
            try:
                query_obj = json.loads(query)
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, raise
                raise ValueError("OpenSearch executable_query must be a JSON string")

            # Extract index if present
            index = None
            if isinstance(query_obj, dict) and "index" in query_obj:
                index = query_obj.pop("index")

            # If the object already contains 'query' / full body, use it as body
            body = query_obj

            # Build AsyncOpenSearch client from OS_HOST
            parsed = urlparse(settings.OS_HOST)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 9200)
            use_ssl = parsed.scheme in ("https", "http") and parsed.scheme == "https"

            http_auth = None
            if settings.OS_AUTH and ":" in settings.OS_AUTH:
                parts = settings.OS_AUTH.split(":", 1)
                http_auth = (parts[0], parts[1])

            client = AsyncOpenSearch(
                hosts=[{"host": host, "port": port}],
                http_auth=http_auth,
                use_ssl=use_ssl,
                verify_certs=False,
            )

            # Execute search
            resp = await client.search(index=index, body=body, size=limit)

            # Extract _source documents
            hits = resp.get("hits", {}).get("hits", [])
            results = [h.get("_source", h) for h in hits]

            await client.close()

            logger.info("OpenSearch query returned %d documents", len(results))
            return results

        except Exception as e:
            logger.error("OpenSearch query execution failed: %s", e)
            raise


class AnswerSynthesisService:
    """Service for synthesizing natural language answers from query results."""

    @staticmethod
    async def synthesize_answer(
        user_query: str,
        routed_query: RoutedQueryPayload,
        raw_results: list[dict[str, Any]],
    ) -> str:
        """Synthesize a formatted answer using the local LLM.

        Args:
            user_query: Original user question
            routed_query: Routed query details with reasoning
            raw_results: Raw database results

        Returns:
            Natural language answer string
        """
        try:
            llm = ChatOllama(
                model=settings.ROUTING_LLM_MODEL,
                base_url=settings.OLLAMA_BASE_URL,
                temperature=0.5,  # Slightly more creative for formatting
            )

            # Format results as JSON for the LLM
            results_text = json.dumps(raw_results, indent=2, default=str)

            prompt = f"""You are a security analyst assistant. A user asked a question and a database query was executed.

User Question: {user_query}

Database Query Explanation: {routed_query.reasoning}

Query Results (JSON):
{results_text}

Please provide a clear, concise summary of the query results that directly answers the user's question.
Format your response as a professional security analysis summary.
If there are no results, explain that no matching data was found.
Keep the answer to 2-3 sentences maximum.

Summary:"""

            message = await llm.ainvoke(prompt)
            formatted_answer = message.content

            logger.info("Answer synthesis complete")
            return formatted_answer

        except Exception as e:
            logger.error("Answer synthesis failed: %s", e)
            # Fallback: return raw results count
            return (
                f"Query completed. Retrieved {len(raw_results)} results from "
                f"{routed_query.target_db}."
            )


class RAGService:
    """Main RAG service orchestrator for semantic routing and query execution."""

    def __init__(self):
        """Initialize RAG service with dependent services."""
        self.query_executor = QueryExecutionService()
        self.answer_synthesizer = AnswerSynthesisService()

    async def process_query(
        self,
        user_query: str,
        filters: Optional[dict[str, Any]] = None,
        limit: int = 10,
    ) -> RAGQueryResponse:
        """Process a semantic RAG query end-to-end.

        Args:
            user_query: Natural language query from analyst
            filters: Optional additional filters (not yet integrated)
            limit: Maximum results to return

        Returns:
            RAGQueryResponse with routed query, raw results, and formatted answer
        """
        try:
            logger.info("RAG query received: %s", user_query)

            # Step 1: Generate routed query using semantic routing
            query_engine = get_query_engine()
            routed_query: RoutedQueryPayload = await query_engine.generate_query(
                user_query
            )

            logger.info(
                "Routed to %s.%s with reasoning: %s",
                routed_query.target_db,
                routed_query.target_source,
                routed_query.reasoning,
            )

            # Step 2: Execute query based on target database
            if routed_query.target_db == "postgresql":
                raw_results = await self.query_executor.execute_postgresql_query(
                    routed_query.executable_query,
                    limit=limit,
                )
            elif routed_query.target_db == "opensearch":
                raw_results = await self.query_executor.execute_opensearch_query(
                    routed_query.executable_query,
                    limit=limit,
                )
            else:
                raise ValueError(
                    f"Unknown target database: {routed_query.target_db}. "
                    f"Must be 'postgresql' or 'opensearch'."
                )

            logger.info(
                "Retrieved %d results from %s",
                len(raw_results),
                routed_query.target_db,
            )

            # Step 3: Synthesize formatted answer using LLM
            formatted_answer = await self.answer_synthesizer.synthesize_answer(
                user_query=user_query,
                routed_query=routed_query,
                raw_results=raw_results,
            )

            logger.info("RAG query completed successfully")

            return RAGQueryResponse(
                routed_query=routed_query,
                raw_results=raw_results,
                formatted_answer=formatted_answer,
            )

        except Exception as e:
            logger.error("RAG query processing failed: %s", e)
            raise


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
