from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    text: str
    document_id: UUID
    document_title: str
    score: float
    chunk_index: int

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    message: Optional[str] = None

class ChunkMetadata(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    company_name: Optional[str] = None

class ContextChunk(BaseModel):
    text: str
    chunk_index: int
    metadata: ChunkMetadata

class DocumentContextResponse(BaseModel):
    document_id: UUID
    chunks: List[ContextChunk]
    total_chunks: int
