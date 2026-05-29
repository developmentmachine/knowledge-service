from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.domain.models.core import Chunk, Document, QueryContext, RetrievalResult

class BaseEmbedder(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Convert single text to embedding vector."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embedding vectors."""
        pass

class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, chunks: List[Chunk]) -> None:
        """Add chunks to the vector store."""
        pass

    @abstractmethod
    def search(self, query_vector: List[float], scopes: List[str], top_k: int = 5) -> List[RetrievalResult]:
        """Search vector store by embedding, scoped by project_ids."""
        pass

class BaseParser(ABC):
    @abstractmethod
    def parse_and_chunk(self, document: Document) -> List[Chunk]:
        """Parse a document and split it into chunks with metadata."""
        pass
