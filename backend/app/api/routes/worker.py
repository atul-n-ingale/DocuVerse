import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.document import ProcessingStatus
from app.services.document_service import get_document_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


class WorkerStatusUpdate(BaseModel):
    task_id: str
    document_id: str
    operation_type: Optional[str] = "processing"  # "deletion" | "processing"
    # Default to processing for backward compatibility
    status: str
    chunks: List[Any]
    error: Optional[str] = None
    # Additional progress fields from worker
    progress: Optional[int] = None
    stage: Optional[str] = None
    message: Optional[str] = None
    current: Optional[int] = None
    total: Optional[int] = None
    stage_progress: Optional[float] = None
    total_progress: Optional[float] = None


@router.post("/worker/status")
async def receive_worker_status(update: WorkerStatusUpdate) -> Dict[str, str]:
    """
    Receive status updates from the worker service.
    This endpoint is called by the worker to report processing status.
    """
    logger.info(
        f"Received worker status update: {update.status} "
        f"for document {update.document_id}, "
        f"operation_type: {update.operation_type}"
    )

    try:
        # Map worker status to backend status based on operation type
        if update.operation_type == "deletion":
            if update.status == "completed":
                # Document deleted successfully
                backend_status = ProcessingStatus.COMPLETED
            elif update.status == "failed":
                # Document deletion failed
                backend_status = ProcessingStatus.DELETE_ERROR
            else:
                # Document is being deleted
                backend_status = ProcessingStatus.DELETING
        else:  # processing operation
            status_mapping = {
                "completed": ProcessingStatus.COMPLETED,
                "failed": ProcessingStatus.FAILED,
                "processing": ProcessingStatus.PROCESSING,
                "pending": ProcessingStatus.PENDING,
            }
            backend_status = status_mapping.get(
                update.status, ProcessingStatus.PROCESSING
            )

        # Update document status in backend database
        update_data: Dict[str, Any] = {"chunks_count": len(update.chunks)}

        if update.error:
            update_data["error_message"] = update.error
            logger.error(f"Worker reported error for document {update.document_id}: " f"{update.error}")

        await get_document_service().update_document_status(update.document_id, backend_status, **update_data)

        # Save chunks to chunks collection if processing completed successfully
        if update.status == "completed" and update.chunks:
            logger.info(f"Saving {len(update.chunks)} chunks for document {update.document_id}")
            try:
                # Use the chunks data as sent from worker (preserve rich metadata)
                chunks_data = []
                for chunk in update.chunks:
                    # If chunk is already a dict with metadata, use it as is
                    if isinstance(chunk, dict) and "metadata" in chunk:
                        chunks_data.append(chunk)
                    else:
                        # Fallback for simple string chunks (backward compatibility)
                        chunk_data = {
                            "content": chunk,
                            "chunk_index": len(chunks_data),
                            "document_id": update.document_id,
                            "metadata": {
                                "chunk_index": len(chunks_data),
                                "document_id": update.document_id,
                            },
                        }
                        chunks_data.append(chunk_data)

                await get_document_service().save_chunks(update.document_id, chunks_data)
                logger.info(f"Successfully saved {len(chunks_data)} chunks for document {update.document_id}")
            except Exception as e:
                logger.error(f"Failed to save chunks for document {update.document_id}: {str(e)}")
                # Don't fail the entire status update if chunk saving fails

        # Send WebSocket update to frontend
        logger.info(
            f"Sending WebSocket update for status: {update.status}"
        )

        # Get WebSocket manager from router
        websocket_manager = getattr(router, "websocket_manager", None)
        if not websocket_manager:
            logger.error("WebSocket manager not found on router")
            return {
                "status": "error",
                "message": "WebSocket manager not available",
            }

        logger.info(
            f"Operation: {update.operation_type}, Status: {update.status}, "
            f"Stage: {update.stage}, Message: {update.message}"
        )
        
        if update.status == "completed" and update.operation_type == "processing":
            logger.info(f"Sending processing complete for task {update.task_id}")
            await websocket_manager.send_processing_complete(update.task_id, update.document_id)
        elif update.status == "completed" and update.operation_type == "deletion":
            logger.info(f"Document deletion completed for {update.document_id}")
            await websocket_manager.send_document_deleted_success(update.document_id)
            # Delete the document record from database
            logger.info(
                f"Deleting document {update.document_id} from database"
            )
            await get_document_service().delete_document(update.document_id)
            logger.info(
                f"Successfully deleted document {update.document_id} from database"
            )
        elif update.status == "failed":
            error_msg = update.error or "Processing failed"
            logger.error(f"Sending error notification for task {update.task_id}: " f"{error_msg}")
            await websocket_manager.send_error(update.task_id, error_msg)
        elif update.status == "deletion_completed":
            logger.info(f"Document deletion completed for {update.document_id}")
            await websocket_manager.send_document_deleted_success(update.document_id)
            # Delete the document record from database
            await get_document_service().delete_document(update.document_id)
        elif update.status == "deletion_failed":
            error_msg = update.error or "Document deletion failed"
            logger.error(f"Document deletion failed for {update.document_id}: " f"{error_msg}")
            await websocket_manager.send_document_deleted_failed(update.document_id, error_msg)
            # Mark document as deletion error
            await get_document_service().mark_document_delete_error(update.document_id, error_msg)
        else:
            # Send progress update for processing status
            # Use progress information from worker if available
            progress = update.progress if update.progress is not None else (50 if update.status == "processing" else 0)
            stage = update.stage if update.stage else update.status
            message = update.message if update.message else f"Worker status: {update.status}"

            logger.info(f"Sending progress update for task {update.task_id}: " f"{progress}% - {stage}")
            await websocket_manager.send_progress_update(
                update.task_id,
                progress,
                stage,
                message,
            )

        logger.info(f"Successfully processed worker status update " f"for document {update.document_id}")
        return {"status": "success", "message": "Status update received"}

    except Exception as e:
        logger.error(f"Error processing worker status update: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing status update: {str(e)}",
        )


@router.post("/worker/test-error")
async def test_error_notification() -> Dict[str, str]:
    """
    Test endpoint to verify error notifications work
    """
    logger.info("Testing error notification")

    try:
        # Get WebSocket manager from router
        websocket_manager = getattr(router, "websocket_manager", None)
        if not websocket_manager:
            logger.error("WebSocket manager not found on router")
            raise HTTPException(status_code=500, detail="WebSocket manager not available")

        # Send a test error via WebSocket
        await websocket_manager.send_error("test-task-id", "Test error message from backend")
        logger.info("Test error notification sent successfully")
        return {"status": "success", "message": "Test error notification sent"}

    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error sending test notification: {str(e)}",
        )
