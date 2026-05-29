"""MCP server exposing knowledge-service ingest/retrieve APIs to AI agents."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_BASE_URL = "http://127.0.0.1:8001"
BASE_URL = os.environ.get("KNOWLEDGE_SERVICE_URL", DEFAULT_BASE_URL).rstrip("/")

mcp = FastMCP(
    "knowledge-service",
    instructions=(
        "Enterprise knowledge base for RAG. Call retrieve_knowledge with explicit "
        "scopes (project_id list) before answering questions about internal projects. "
        "Ensure the HTTP API is running (default port 8001)."
    ),
)


def _client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=120.0)


def _format_retrieval_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "No matching knowledge chunks found for this query and scopes."

    parts: list[str] = []
    for i, item in enumerate(results, start=1):
        score = item.get("score", 0.0)
        project_id = item.get("project_id", "unknown")
        file_path = item.get("file_path", "unknown")
        content = item.get("content", "")
        parts.append(
            f"### [{i}] score={score:.4f} | project={project_id}\n"
            f"**Source:** `{file_path}`\n\n"
            f"{content.strip()}\n"
        )
    return "\n---\n\n".join(parts)


@mcp.tool()
def knowledge_health() -> str:
    """Check whether the knowledge-service HTTP API is reachable."""
    try:
        with _client() as client:
            response = client.get("/health")
            response.raise_for_status()
            payload = response.json()
        return f"OK — knowledge-service at {BASE_URL}: {json.dumps(payload)}"
    except httpx.HTTPError as exc:
        return (
            f"Unreachable — cannot connect to {BASE_URL}. "
            f"Start the API first (e.g. `make run` or `docker-compose up`). Error: {exc}"
        )


@mcp.tool()
def retrieve_knowledge(
    query: str,
    scopes: list[str],
    top_k: int = 5,
) -> str:
    """Semantic search over the knowledge base within the given project scopes.

    Args:
        query: Natural language question or keywords.
        scopes: Project IDs to search (required). Example: ["agent-platform", "agent-framework"].
        top_k: Number of chunks to return (1–20).
    """
    if not scopes:
        return "Error: scopes must be a non-empty list of project_id values."

    top_k = max(1, min(top_k, 20))
    body = {
        "query": query,
        "scopes": scopes,
        "top_k": top_k,
        "hybrid_search": True,
    }

    try:
        with _client() as client:
            response = client.post("/api/v1/retrieve", json=body)
            response.raise_for_status()
            results = response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        return f"Retrieve failed ({exc.response.status_code}): {detail}"
    except httpx.HTTPError as exc:
        return f"Cannot reach knowledge-service at {BASE_URL}: {exc}"

    return _format_retrieval_results(results)


@mcp.tool()
def ingest_document(
    project_id: str,
    file_path: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Ingest a single document into the knowledge base (parse, embed, store).

    Args:
        project_id: Tenant/project identifier for isolation.
        file_path: Logical source path shown in retrieval results.
        content: Full document text.
        metadata: Optional extra metadata dict.
    """
    body = {
        "project_id": project_id,
        "file_path": file_path,
        "content": content,
        "metadata": metadata or {},
    }

    try:
        with _client() as client:
            response = client.post("/api/v1/ingest", json=body)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        return f"Ingest failed ({exc.response.status_code}): {exc.response.text}"
    except httpx.HTTPError as exc:
        return f"Cannot reach knowledge-service at {BASE_URL}: {exc}"

    chunks = payload.get("chunks_ingested", 0)
    return f"Ingested successfully: {chunks} chunk(s) for project `{project_id}` ({file_path})."


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
