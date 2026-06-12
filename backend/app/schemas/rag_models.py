"""RAG system Pydantic models for request/response contracts."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class RoutedQueryPayload(BaseModel):
    """Result of semantic routing engine."""

    target_db: str = Field(
        ...,
        description="Target database: 'postgresql' or 'opensearch'",
    )
    target_source: str = Field(
        ...,
        description="Target table name (PostgreSQL) or index pattern (OpenSearch)",
    )
    executable_query: str = Field(
        ...,
        description="Generated SQL query (PostgreSQL) or OpenSearch DSL (JSON)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this query was generated and routed to this target",
    )


class RAGQueryRequest(BaseModel):
    """Request body for RAG semantic query endpoint."""

    query: str = Field(
        ...,
        description="Natural language query from security analyst",
        example="What are the top critical incidents from the last 24 hours?",
    )
    filters: Optional[dict[str, Any]] = Field(
        None,
        description="Optional additional filters (key-value pairs)",
    )
    limit: Optional[int] = Field(
        10,
        ge=1,
        le=1000,
        description="Maximum number of results to return",
    )


class RAGQueryResponse(BaseModel):
    """Response body for RAG semantic query endpoint."""

    routed_query: RoutedQueryPayload = Field(
        ...,
        description="Details of how the query was routed and generated",
    )
    raw_results: list[dict[str, Any]] = Field(
        ...,
        description="Raw database results (rows or documents)",
    )
    formatted_answer: str = Field(
        ...,
        description="LLM-synthesized natural language answer to the user's query",
    )


class RAGHealthResponse(BaseModel):
    """Health check response for RAG system."""

    status: str = Field(..., description="Health status: 'healthy', 'initializing', or 'unhealthy'")
    vector_store: Optional[str] = Field(None, description="Vector store status")
    llm_model: Optional[str] = Field(None, description="Active LLM model")
    embedding_model: Optional[str] = Field(None, description="Active embedding model")
    message: Optional[str] = Field(None, description="Additional status message")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
