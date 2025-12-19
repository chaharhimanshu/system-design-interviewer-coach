"""
Pydantic models for request/response validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for querying the bot"""

    query: str
    session_id: Optional[str] = None  # Optional session ID for conversation memory


class QueryResponse(BaseModel):
    """Response model for query results"""

    query: str
    answer: str
    steps_used: List[str]
    timestamp: str
    session_id: str  # Return session ID for tracking conversation


class UploadResponse(BaseModel):
    """Response model for PDF upload"""

    message: str
    filename: str
    chunks_created: int
    vectorstore_updated: bool


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str
    vectorstore_loaded: bool
    documents_count: int


class VectorStoreDocument(BaseModel):
    """Model for a single document in vectorstore"""

    content: str
    metadata: Dict[str, Any]
    similarity_score: Optional[float] = None


class VectorStoreDataResponse(BaseModel):
    """Response model for vectorstore data"""

    total_documents: int
    documents: List[VectorStoreDocument]
    message: str
