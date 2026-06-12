"""RAG router endpoints for semantic query generation and execution.

This router provides thin endpoints that orchestrate the RAG service.
All business logic is delegated to the RAGService layer.
"""

import logging
from fastapi import APIRouter, HTTPException

from app.schemas.rag_models import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGHealthResponse,
)
from app.services.rag_service import get_rag_service
from app.services.vector_manager import get_vector_manager
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["RAG"])


@router.post(
    "/api/v1/rag/query",
    response_model=RAGQueryResponse,
    summary="Semantic RAG Query Endpoint",
    description="Execute a natural language query with semantic routing to the appropriate database",
)
async def rag_query(request: RAGQueryRequest) -> RAGQueryResponse:
    """Execute semantic routing and query generation.

    Takes a natural language query from a security analyst, routes it to the appropriate
    database (PostgreSQL or OpenSearch), generates and executes the query, and returns
    a formatted natural language answer.

    Args:
        request: RAGQueryRequest containing user query, optional filters, and limit

    Returns:
        RAGQueryResponse with routed query details, raw results, and formatted answer

    Raises:
        HTTPException: 500 if query processing fails
    """
    try:
        rag_service = get_rag_service()
        response = await rag_service.process_query(
            user_query=request.query,
            filters=request.filters,
            limit=request.limit or 10,
        )
        return response

    except Exception as e:
        logger.error("RAG query endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/v1/rag/health",
    response_model=RAGHealthResponse,
    summary="RAG System Health Check",
    description="Check health and readiness of the RAG system",
)
async def rag_health() -> RAGHealthResponse:
    """Health check for RAG system components.

    Returns:
        RAGHealthResponse with status of vector store and LLM components
    """
    try:
        vector_manager = get_vector_manager()

        if not vector_manager._initialized:
            return RAGHealthResponse(
                status="initializing",
                message="Vector manager not yet initialized",
            )

        return RAGHealthResponse(
            status="healthy",
            vector_store="ready",
            llm_model=settings.ROUTING_LLM_MODEL,
            embedding_model=settings.EMBEDDING_MODEL,
        )

    except Exception as e:
        logger.error("RAG health check failed: %s", e)
        return RAGHealthResponse(
            status="unhealthy",
            error=str(e),
        )
