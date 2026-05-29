from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.repositories.interfaces import BaseParser
from app.domain.models.core import Document, Chunk, ChunkMetadata

class MarkdownParser(BaseParser):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def parse_and_chunk(self, document: Document) -> List[Chunk]:
        texts = self.text_splitter.split_text(document.content)
        
        chunks = []
        for text in texts:
            metadata = ChunkMetadata(
                project_id=document.project_id,
                file_path=document.file_path,
                chunk_type="markdown",
                extra=document.metadata
            )
            chunks.append(Chunk(content=text, metadata=metadata))
            
        return chunks
