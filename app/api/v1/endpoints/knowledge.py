from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from functools import lru_cache

from app.domain.models.core import Document, QueryContext, RetrievalResult
from app.services.knowledge_service import KnowledgeService
from app.infrastructure.embedding.sentence_transformer import SentenceTransformerEmbedder
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from app.infrastructure.parsing.markdown_parser import MarkdownParser

router = APIRouter()

# Dependency Injection (Singleton pattern using lru_cache)
@lru_cache()
def get_knowledge_service() -> KnowledgeService:
    # Initialize dependencies only once
    embedder = SentenceTransformerEmbedder()
    vector_store = ChromaVectorStore()
    parser = MarkdownParser()
    return KnowledgeService(vector_store, embedder, parser)


class IngestRequest(BaseModel):
    project_id: str
    file_path: str
    content: str
    metadata: dict = {}

class RetrieveRequest(BaseModel):
    query: str
    scopes: List[str]
    hybrid_search: bool = True
    top_k: int = 5


@router.post("/ingest", response_model=dict)
def ingest_document(req: IngestRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    doc = Document(
        project_id=req.project_id,
        file_path=req.file_path,
        content=req.content,
        metadata=req.metadata
    )
    try:
        chunks_count = service.ingest_document(doc)
        return {"status": "success", "chunks_ingested": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=List[RetrievalResult])
def retrieve_knowledge(req: RetrieveRequest, service: KnowledgeService = Depends(get_knowledge_service)):
    query_context = QueryContext(
        query=req.query,
        scopes=req.scopes,
        hybrid_search=req.hybrid_search,
        top_k=req.top_k
    )
    try:
        results = service.retrieve(query_context)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
