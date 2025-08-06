from typing import Any, Dict

from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.services.document_deletion_service import delete_document_vectors
from app.services.document_processor_service import process_document

# Get Celery logger for this task
logger = get_task_logger(__name__)


@celery_app.task(
    bind=True, name="app.tasks.process_document_task"
)  # type: ignore[misc]
def process_document_task(
    self: Any, task_id: str, file_path: str, document_id: str
) -> Dict[str, Any]:
    """
    Celery task to process documents. Properly handles exceptions and logging.
    """
    logger.info(
        f"Starting document processing task: {task_id} " f"for document: {document_id}"
    )

    try:
        result = process_document(task_id, file_path, document_id)

        logger.info(f"Process document returned result: {result}")

        # Check if the result indicates an error
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(
                f"Document processing failed for {document_id}: {error_msg}",
                exc_info=True,
            )
            # Raise an exception to mark the task as failed in Celery
            raise Exception(f"Document processing failed: {error_msg}")

        logger.info(f"Document processing completed successfully for {document_id}")
        logger.info(f"Returning result: {result}")
        return result

    except Exception as e:
        logger.error(f"Task failed for document {document_id}: {str(e)}", exc_info=True)
        # Re-raise the exception to ensure Celery marks the task as failed
        raise


@celery_app.task(bind=True, name="app.tasks.delete_document_task")  # type: ignore[misc]
def delete_document_task(self: Any, document_id: str) -> Dict[str, Any]:
    """
    Celery task to delete document vectors from Pinecone and report status.
    """
    task_id = self.request.id
    logger.info(f"Starting document deletion task: {task_id} for document: {document_id}")

    try:
        result = delete_document_vectors(document_id, task_id)

        logger.info(f"Delete document returned result: {result}")

        # Check if the result indicates an error
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(
                f"Document deletion failed for {document_id}: {error_msg}",
                exc_info=True,
            )
            # Raise an exception to mark the task as failed in Celery
            raise Exception(f"Document deletion failed: {error_msg}")

        logger.info(f"Document deletion completed successfully for {document_id}")
        logger.info(f"Returning result: {result}")
        return result

    except Exception as e:
        logger.error(
            f"Delete task failed for document {document_id}: {str(e)}", exc_info=True
        )
        # Re-raise the exception to ensure Celery marks the task as failed
        raise
