from typing import Dict, List

from fastapi import APIRouter, HTTPException

from app.core.celery_client import get_celery_client
from app.models.document import Document, ProcessingStatus
from app.services.document_service import get_document_service

router = APIRouter()


@router.get("/documents", response_model=List[Document])
async def get_documents() -> List[Document]:
    """Get all uploaded documents"""
    try:
        documents = await get_document_service().get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: str) -> Document:
    """Get a specific document by ID"""
    try:
        document = await get_document_service().get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str) -> Dict[str, str]:
    """Delete a document and its associated data"""
    try:
        document = await get_document_service().get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Mark document as deleting
        await get_document_service().mark_document_deleting(document_id)

        # Emit WebSocket event
        websocket_manager = getattr(router, "websocket_manager", None)
        if websocket_manager:
            await websocket_manager.send_document_deletion_started(document_id)

        # Submit Celery task to delete document vectors
        celery_client = get_celery_client()
        task = celery_client.send_task("app.tasks.delete_document_task", args=[document_id])

        return {"message": "Document deletion started", "task_id": task.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
