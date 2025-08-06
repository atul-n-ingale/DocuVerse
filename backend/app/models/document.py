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
