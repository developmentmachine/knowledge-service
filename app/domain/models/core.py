from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class ChunkMetadata(BaseModel):
    project_id: str
    file_path: str
    chunk_type: str
    semantic_tags: List[str] = Field(default_factory=list)
    importance_score: float = 1.0
    extra: Dict[str, Any] = Field(default_factory=dict)

class Chunk(BaseModel):
    chunk_id: UUID = Field(default_factory=uuid4)
    content: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None

class Document(BaseModel):
    doc_id: UUID = Field(default_factory=uuid4)
    project_id: str
    file_path: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueryContext(BaseModel):
    query: str
    scopes: List[str]
    hybrid_search: bool = True
    top_k: int = 5

class RetrievalResult(BaseModel):
    chunk_id: UUID
    project_id: str
    file_path: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
