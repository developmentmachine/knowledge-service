from typing import List
from loguru import logger

from app.domain.models.core import Document, Chunk, QueryContext, RetrievalResult
from app.domain.repositories.interfaces import BaseVectorStore, BaseEmbedder, BaseParser

class KnowledgeService:
    def __init__(
        self, 
        vector_store: BaseVectorStore, 
        embedder: BaseEmbedder, 
        parser: BaseParser
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.parser = parser

    def ingest_document(self, document: Document) -> int:
        """Parse document, embed chunks, and store them."""
        logger.info(f"Ingesting document from {document.file_path} for project {document.project_id}")
        
        # 1. Parse and Chunk
        chunks = self.parser.parse_and_chunk(document)
        if not chunks:
            logger.warning(f"No chunks extracted from {document.file_path}")
            return 0
            
        # 2. Embed
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_batch(texts)
        
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
            
        # 3. Store
        self.vector_store.add(chunks)
        logger.info(f"Successfully ingested {len(chunks)} chunks.")
        
        return len(chunks)

    def retrieve(self, query_context: QueryContext) -> List[RetrievalResult]:
        """Retrieve relevant chunks based on query and scopes."""
        logger.info(f"Retrieving for query: '{query_context.query}' in scopes: {query_context.scopes}")
        
        # 1. Embed Query
        query_vector = self.embedder.embed_text(query_context.query)
        
        # 2. Search Vector Store
        results = self.vector_store.search(
            query_vector=query_vector,
            scopes=query_context.scopes,
            top_k=query_context.top_k
        )
        
        # TODO: Add BM25 Hybrid Search and Re-ranking for V2.0+
        
        return results
