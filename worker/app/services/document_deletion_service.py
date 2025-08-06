import logging
from typing import Any, Dict, Optional

import pinecone
import requests

from app.config import BACKEND_URL, PINECONE_API_KEY, PINECONE_INDEX

# Get logger
logger = logging.getLogger(__name__)


def delete_document_vectors(document_id: str) -> Dict[str, Any]:
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

        # Initialize Pinecone
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)

        # Report deletion started
        report_deletion_status_to_backend(document_id, "deleting", 0)

        # First, try to query for vectors with document_id prefix in their IDs
        logger.info(f"Querying for vectors with document_id prefix: {document_id}")

        # Use Pinecone query to find all vectors for this document
        # Try both metadata filtering and ID pattern matching
        query_response = index.query(
            vector=[0] * 1536,  # Dummy vector for metadata-only query
            filter={"document_id": {"$eq": document_id}},
            include_metadata=True,
            top_k=10000,  # Large number to get all vectors
        )

        vector_ids = []
        if query_response.matches:
            # Extract vector IDs to delete
            vector_ids = [match.id for match in query_response.matches]
            logger.info(
                f"Found {len(vector_ids)} vectors to delete for document {document_id}"
            )

        if vector_ids:
            # Delete vectors in batches (Pinecone has limits on batch size)
            batch_size = 100
            deleted_count = 0

            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i : i + batch_size]
                logger.info(f"Deleting batch {i//batch_size + 1}: {len(batch)} vectors")
                logger.debug(f"Batch vector IDs: {batch}")

                # Delete the batch
                index.delete(ids=batch)
                deleted_count += len(batch)

                # Report progress
                progress = int((deleted_count / len(vector_ids)) * 100)
                report_deletion_status_to_backend(document_id, "deleting", progress)

            result["deleted_vectors"] = deleted_count
            logger.info(
                f"Successfully deleted {deleted_count} vectors for document {document_id}"
            )

        else:
            logger.info(f"No vectors found for document {document_id}")

        # Report successful completion
        report_deletion_status_to_backend(document_id, "deletion_completed", 100)

    except Exception as e:
        logger.error(
            f"Error deleting vectors for document {document_id}: {str(e)}",
            exc_info=True,
        )
        result["status"] = "error"
        result["error"] = str(e)

        # Report error to backend
        try:
            report_deletion_status_to_backend(
                document_id, "deletion_failed", 0, error=str(e)
            )
        except Exception as report_error:
            logger.error(f"Failed to report error status: {str(report_error)}")

    return result


def report_deletion_status_to_backend(
    document_id: str,
    status: str,
    progress: int,
    error: Optional[str] = None,
) -> None:
    """Report deletion status to backend via REST API"""
    try:
        payload: Dict[str, Any] = {
            "task_id": f"delete_{document_id}",
            "document_id": document_id,
            "status": status,
            "chunks": [],  # Empty list for deletion operations
            "error": error,
        }

        logger.info(f"Reporting deletion status to backend: {status} for {document_id}")

        response = requests.post(
            f"{BACKEND_URL}/worker/status",
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            logger.info(f"Successfully reported deletion status: {status}")
        else:
            logger.error(
                f"Failed to report deletion status. "
                f"Status code: {response.status_code}, "
                f"Response: {response.text}"
            )

    except Exception as e:
        logger.error(f"Error reporting deletion status to backend: {str(e)}")
