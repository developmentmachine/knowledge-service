from typing import List
from sentence_transformers import SentenceTransformer
from app.domain.repositories.interfaces import BaseEmbedder

class SentenceTransformerEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding model. 
        Downloads the model on first run.
        """
        self.model = SentenceTransformer(model_name)

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
