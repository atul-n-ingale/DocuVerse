import os
from typing import Any, Dict, List, Optional

import pinecone
import pymongo
import requests
from celery.utils.log import get_task_logger

from app.config import BACKEND_URL, MONGODB_URI, PINECONE_API_KEY, PINECONE_INDEX
from app.core.progress_manager import ProgressManager

# Get Celery logger
logger = get_task_logger(__name__)


# Modular service-based architecture for document processing


def process_document(task_id: str, file_path: str, document_id: str) -> Dict[str, Any]:
    """
    Main entrypoint for Celery task: process a document using LlamaIndex workflow.
    Supports PDF, image, and CSV files with unified metadata and node management.
    Now includes live progress updates via ProgressManager.
    """
    import logging

    from .document_ingestor import DocumentIngestor

    logger = logging.getLogger("DocumentProcessorService")
    logger.info(f"Processing document {document_id} with file {file_path}")

    # Create progress manager for live updates
    progress_manager = ProgressManager(
        backend_url=BACKEND_URL,
        document_id=document_id,
        task_id=task_id
    )

    try:
        # Report processing started
        progress_manager.report_status_to_backend("processing")
        
        # Use the new LlamaIndex workflow-based ingestor with progress tracking
        ingestor = DocumentIngestor(document_id, file_path, progress_manager)
        num_chunks = ingestor.ingest()
        logger.info(
            f"Successfully processed document {document_id} with {num_chunks} chunks"
        )
        
        # Completion is handled by DocumentIngestor with chunks data
        return {"status": "success", "document_id": document_id, "chunks": num_chunks}
    except Exception as e:
        logger.error(
            f"Error processing document {document_id}: {str(e)}", exc_info=True
        )
        
        # Error reporting is handled by DocumentIngestor
        return {"status": "error", "document_id": document_id, "error": str(e)}


def upsert_pinecone(
    document_id: str, embeddings: List[List[float]], chunks: List[str]
) -> None:
    logger.info(
        f"Upserting {len(embeddings)} vectors to Pinecone for document "
        f"{document_id}"
    )

    # Validate Pinecone configuration
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not configured")

    if not PINECONE_INDEX:
        raise ValueError("PINECONE_INDEX is not configured")

    logger.info(f"Using Pinecone index: {PINECONE_INDEX}")

    try:
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX)
        vectors = [
            (
                f"{document_id}_{i}",
                emb,
                {"chunk": chunk, "document_id": document_id, "chunk_index": i},
            )
            for i, (emb, chunk) in enumerate(zip(embeddings, chunks))
        ]
        index.upsert(vectors=vectors)
        logger.info(
            f"Successfully upserted vectors to Pinecone for document " f"{document_id}"
        )

    except Exception as e:
        logger.error(
            f"Failed to upsert to Pinecone for document {document_id}: " f"{str(e)}",
            exc_info=True,
        )
        raise


def save_workflow_state(document_id: str, state: Dict[str, Any]) -> None:
    client: pymongo.MongoClient[Any] = pymongo.MongoClient(MONGODB_URI)
    db = client.get_default_database()
    collection = db.document_workflows
    collection.update_one({"document_id": document_id}, {"$set": state}, upsert=True)
    client.close()


# Note: report_status_to_backend function has been merged into ProgressManager
# Use progress_manager.report_status_to_backend() instead
