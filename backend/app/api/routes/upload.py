import os
import uuid
from typing import Any, Dict, List

import aiofiles
from celery import Celery
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.document import DocumentCreate, DocumentType, UploadResponse
from app.services.document_service import get_document_service

celery_app = Celery("docuverse", broker="redis://redis:6379/0")

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)) -> UploadResponse:
    """Upload a document for processing"""

    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    supported_extensions = [".pdf", ".docx", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg"]

    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {supported_extensions}",
        )

    # Determine document type
    type_mapping = {
        ".pdf": DocumentType.PDF,
        ".docx": DocumentType.DOCX,
        ".csv": DocumentType.CSV,
        ".xlsx": DocumentType.EXCEL,
        ".xls": DocumentType.EXCEL,
        ".png": DocumentType.IMAGE,
        ".jpg": DocumentType.IMAGE,
        ".jpeg": DocumentType.IMAGE,
    }

    document_type = type_mapping[file_extension]

    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"

    # Create upload directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)

    # Save file
    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Create document record
    document_data = DocumentCreate(
        filename=file.filename,
        file_type=document_type,
        file_size=len(content),
        task_id=file_id,
    )

    document = await get_document_service().create_document(document_data)

    # Start processing task using the new worker's Celery task name
    celery_app.send_task(
        "app.tasks.process_document_task",
        args=[file_id, file_path, document.id],
    )

    return UploadResponse(
        task_id=file_id,
        filename=file.filename,
        message="File uploaded successfully. Processing started.",
    )


@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)) -> Dict[str, List[Any]]:
    """Upload multiple documents for processing"""
    results: List[Any] = []

    for file in files:
        try:
            result = await upload_file(file)
            results.append(result.model_dump())
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    return {"results": results}
