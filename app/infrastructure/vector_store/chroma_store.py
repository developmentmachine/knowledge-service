import chromadb
from chromadb.config import Settings
from typing import List
import uuid

from app.domain.repositories.interfaces import BaseVectorStore
from app.domain.models.core import Chunk, RetrievalResult

class ChromaVectorStore(BaseVectorStore):
    def __init__(self, persist_directory: str = "./data/chroma", collection_name: str = "knowledge_base"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add(self, chunks: List[Chunk]) -> None:
        if not chunks:
            return

        ids = [str(chunk.chunk_id) for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks if chunk.embedding is not None]
        
        # Format metadata for Chroma (cannot handle complex nested dicts easily, flatten them)
        metadatas = []
        for chunk in chunks:
            meta = {
                "project_id": chunk.metadata.project_id,
                "file_path": chunk.metadata.file_path,
                "chunk_type": chunk.metadata.chunk_type,
                "importance_score": chunk.metadata.importance_score
            }
            # Add semantic tags as comma separated string
            if chunk.metadata.semantic_tags:
                meta["semantic_tags"] = ",".join(chunk.metadata.semantic_tags)
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            embeddings=embeddings if len(embeddings) == len(chunks) else None,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query_vector: List[float], scopes: List[str], top_k: int = 5) -> List[RetrievalResult]:
        
        # Build where filter based on scopes (projects)
        where_filter = {}
        if scopes and "*" not in scopes:
            if len(scopes) == 1:
                where_filter = {"project_id": scopes[0]}
            else:
                where_filter = {"project_id": {"$in": scopes}}

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        retrieval_results = []
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                doc_id = results['ids'][0][i]
                metadata = results['metadatas'][0][i]
                content = results['documents'][0][i]
                
                # Chroma returns distance. If cosine, distance = 1 - cosine_similarity.
                # We want a similarity score where higher is better.
                distance = results['distances'][0][i] if results['distances'] else 0.0
                score = 1.0 - distance

                retrieval_results.append(RetrievalResult(
                    chunk_id=uuid.UUID(doc_id),
                    project_id=metadata.get("project_id", "unknown"),
                    file_path=metadata.get("file_path", "unknown"),
                    content=content,
                    score=score,
                    metadata=metadata
                ))

        return retrieval_results
