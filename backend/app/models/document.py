from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETING = "deleting"
    DELETE_ERROR = "delete_error"


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    EXCEL = "excel"
    IMAGE = "image"


class DocumentBase(BaseModel):
    filename: str
    file_type: DocumentType
    file_size: int
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    status: ProcessingStatus = ProcessingStatus.PENDING
    task_id: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: str
    chunks_count: int = 0
    processing_start_time: Optional[datetime] = None
    processing_end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DocumentChunk(BaseModel):
    id: str = Field(alias="_id")
    document_id: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    section: Optional[str] = None
    embedding_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True


class QueryRequest(BaseModel):
    query: str
    max_results: int = 5
    include_sources: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    processing_time: float = 0.0


class UploadResponse(BaseModel):
    task_id: str
    filename: str
    message: str


# Enhanced Q&A System Models
class ConversationSession(BaseModel):
    id: str
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    title: str
    is_active: bool = True
    message_count: int = 0


class ConversationMessage(BaseModel):
    id: str
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}  # For storing sources, confidence, reasoning steps, etc.


class EnhancedQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    max_results: int = 5
    include_sources: bool = True
    include_reasoning: bool = True
    conversation_history: Optional[List[Dict[str, Any]]] = None


class EnhancedQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    confidence: float = 0.0
    processing_time: float = 0.0
    session_id: str
    reasoning_steps: List[str] = []
    conversation_history: List[Dict[str, Any]] = []


class ConversationSessionCreate(BaseModel):
    title: str
    user_id: Optional[str] = None


class ConversationSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool
