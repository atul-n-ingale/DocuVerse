import logging
from typing import Any, Dict

from app.config import BACKEND_URL, PINECONE_API_KEY, PINECONE_INDEX
from app.core.lib.llamaindex import CustomPineconeVectorStore
from app.core.progress_manager import ProgressManager

# Get logger
logger = logging.getLogger(__name__)


def delete_document_vectors(document_id: str, task_id: str) -> Dict[str, Any]:
    """
    Delete all vectors associated with a document from Pinecone.
    Uses hierarchical IDs with document_id prefix for efficient deletion.
    """
    logger.info(f"Starting deletion of vectors for document: {document_id}")

    result: Dict[str, Any] = {
        "status": "success",
        "document_id": document_id,
        "deleted_vectors": 0,
        "error": None,
    }

    try:
        # Validate Pinecone configuration
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not configured")

        if not PINECONE_INDEX:
            raise ValueError("PINECONE_INDEX is not configured")

        logger.info(f"Using Pinecone index: {PINECONE_INDEX}")

        # Initialize CustomPineconeVectorStore
        vector_store = CustomPineconeVectorStore(
            index_name=PINECONE_INDEX,
            api_key=PINECONE_API_KEY,
            environment="gcp-starter",
            namespace="",
            insert_kwargs={},
            add_sparse_vector=False,
            text_key="text",
            batch_size=100,
            remove_text_from_metadata=False,
        )

        # Initialize ProgressManager for status reporting
        progress_manager = ProgressManager(
            backend_url=BACKEND_URL,
            document_id=document_id,
            task_id=task_id,
            operation_type="deletion",
        )

        # Start deletion stage
        progress_manager.start_stage("deletion")

        # Get progress callback
        progress_callback = progress_manager.get_progress_callback()

        # Delete document using CustomPineconeVectorStore
        deletion_result = vector_store.delete_document(
            document_id=document_id, progress_callback=progress_callback
        )

        # Update result with deletion results
        result.update(deletion_result)

        if result["status"] == "success":
            # Complete the stage successfully
            progress_manager.complete_stage("deletion")

            # Send final progress update with completion status
            logger.info(f"Sending final completion status for document {document_id}")
            progress_manager.send_final_progress_update(
                status="completed", 
                chunks=[]  # Empty chunks for deletion
            )
            logger.info(f"Final completion status sent for document {document_id}")
        else:
            # Report error status
            progress_manager.send_final_progress_update(
                status="failed", error=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(
            f"Error deleting vectors for document {document_id}: " f"{str(e)}",
            exc_info=True,
        )
        result["status"] = "error"
        result["error"] = str(e)

        # Report error to backend using ProgressManager if available
        try:
            if 'progress_manager' in locals():
                progress_manager.send_final_progress_update(status="failed", error=str(e))
            else:
                # Create a new ProgressManager with a fallback task_id
                fallback_task_id = f"delete_{document_id}"
                progress_manager = ProgressManager(
                    backend_url=BACKEND_URL,
                    document_id=document_id,
                    task_id=fallback_task_id,
                    operation_type="deletion",
                )
                progress_manager.send_final_progress_update(status="failed", error=str(e))
        except Exception as report_error:
            logger.error(f"Failed to report error status: {str(report_error)}")

    return result
