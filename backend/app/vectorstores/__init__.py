"""Semantic Router and Text-to-Query RAG System

This module provides a semantic routing system that:
1. Takes natural language queries from users
2. Retrieves relevant database schema metadata from Qdrant
3. Generates precise SQL or OpenSearch DSL queries using a local LLM (Ollama)
4. Executes the query against the appropriate database
5. Synthesizes a formatted answer using the LLM

All components are local and containerized for privacy and speed.
"""
