"""
Integration tests for document deletion and chunk management.
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Patch Pinecone/VectorStore before importing anything that uses it
sys.modules["app.services.vector_store"] = MagicMock()

from app.models.document import ProcessingStatus


@pytest.mark.integration
class TestDocumentDeletionIntegration:
    """Integration tests for document deletion flow."""

    @pytest.mark.asyncio
    async def test_document_deletion_flow(self, sync_client):
        """Test complete document deletion flow."""
        document_id = "test-doc-123"

        # Mock document service
        with patch("app.api.routes.documents.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_doc = MagicMock()
            mock_doc.id = document_id
            mock_doc.filename = "test.pdf"
            mock_service.get_document.return_value = mock_doc
            mock_get_service.return_value = mock_service

            # Mock Celery client
            with patch("app.api.routes.documents.get_celery_client") as mock_celery:
                mock_celery_client = MagicMock()
                mock_task = MagicMock()
                mock_task.id = "delete-task-123"
                mock_celery_client.send_task.return_value = mock_task
                mock_celery.return_value = mock_celery_client

                # Mock WebSocket manager
                with patch("app.api.routes.documents.getattr") as mock_getattr:
                    mock_websocket = AsyncMock()
                    mock_getattr.return_value = mock_websocket

                    # Test DELETE endpoint
                    response = sync_client.delete(f"/api/documents/{document_id}")

                    # Verify response
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data["message"] == "Document deletion started"
                    assert response_data["task_id"] == "delete-task-123"

                    # Verify document service was called
                    mock_service.mark_document_deleting.assert_called_once_with(document_id)

                    # Verify Celery task was called
                    mock_celery_client.send_task.assert_called_once_with(
                        "app.tasks.delete_document_task", args=[document_id]
                    )

                    # Verify WebSocket event was sent
                    mock_websocket.send_document_deletion_started.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_document_deletion_not_found(self, sync_client):
        """Test document deletion when document doesn't exist."""
        # Mock document service to return None
        with patch("app.api.routes.documents.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_document.return_value = None
            mock_get_service.return_value = mock_service

            response = sync_client.delete("/api/documents/non-existent-id")
            assert response.status_code == 404
            assert "Document not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_worker_deletion_completed_status(self, sync_client):
        """Test worker status update for successful document deletion."""
        document_id = "test-doc-123"

        # Mock document service
        with patch("app.api.routes.worker.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service

            # Mock WebSocket manager
            with patch("app.api.routes.worker.getattr") as mock_getattr:
                mock_websocket = AsyncMock()
                mock_getattr.return_value = mock_websocket

                # Send worker status update for deletion completed
                status_update = {
                    "task_id": "delete-task-123",
                    "document_id": document_id,
                    "status": "deletion_completed",
                    "chunks": [],
                    "error": None,
                }

                response = sync_client.post("/api/worker/status", json=status_update)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["status"] == "success"

                # Verify document and chunks are deleted
                mock_service.delete_document.assert_called_once_with(document_id)

                # Verify WebSocket event was sent
                mock_websocket.send_document_deleted_success.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_worker_deletion_failed_status(self, sync_client):
        """Test worker status update for failed document deletion."""
        document_id = "test-doc-123"

        # Mock document service
        with patch("app.api.routes.worker.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service

            # Mock WebSocket manager
            with patch("app.api.routes.worker.getattr") as mock_getattr:
                mock_websocket = AsyncMock()
                mock_getattr.return_value = mock_websocket

                # Send worker status update for deletion failed
                status_update = {
                    "task_id": "delete-task-123",
                    "document_id": document_id,
                    "status": "deletion_failed",
                    "chunks": [],
                    "error": "Pinecone deletion failed",
                }

                response = sync_client.post("/api/worker/status", json=status_update)

                # Verify response
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["status"] == "success"

                # Verify document is marked as deletion error
                mock_service.mark_document_delete_error.assert_called_once_with(document_id, "Pinecone deletion failed")

                # Verify WebSocket event was sent
                mock_websocket.send_document_deleted_failed.assert_called_once_with(
                    document_id, "Pinecone deletion failed"
                )

    @pytest.mark.asyncio
    async def test_worker_processing_completed_with_chunks(self, sync_client):
        """Test worker status update for completed processing with chunk saving."""
        document_id = "test-doc-789"

        # Mock document service
        with patch("app.api.routes.worker.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value = mock_service

            # Mock WebSocket manager
            with patch("app.api.routes.worker.getattr") as mock_getattr:
                mock_websocket = AsyncMock()
                mock_getattr.return_value = mock_websocket

                # Send worker status update for completed processing
                status_update = {
                    "task_id": "test-task-789",
                    "document_id": document_id,
                    "status": "completed",
                    "chunks": ["Chunk 1 content", "Chunk 2 content"],
                    "error": None,
                }

                response = sync_client.post("/api/worker/status", json=status_update)

                # Verify response
                assert response.status_code == 200

                # Verify document status is updated
                mock_service.update_document_status.assert_called_once()
                call_args = mock_service.update_document_status.call_args
                assert call_args[0][0] == document_id  # document_id
                assert call_args[0][1] == ProcessingStatus.COMPLETED  # status
                assert call_args[1]["chunks_count"] == 2  # chunks_count

                # Verify chunks are saved
                mock_service.save_chunks.assert_called_once()
                save_call_args = mock_service.save_chunks.call_args
                assert save_call_args[0][0] == document_id  # document_id
                chunks_data = save_call_args[0][1]  # chunks
                assert len(chunks_data) == 2
                assert chunks_data[0]["content"] == "Chunk 1 content"
                assert chunks_data[0]["chunk_index"] == 0
                assert chunks_data[1]["content"] == "Chunk 2 content"
                assert chunks_data[1]["chunk_index"] == 1

                # Verify WebSocket event was sent
                mock_websocket.send_processing_complete.assert_called_once_with("test-task-789", document_id)

    @pytest.mark.asyncio
    async def test_get_document_chunks_endpoint(self, sync_client):
        """Test the GET /documents/{id}/chunks endpoint."""
        document_id = "test-doc-123"

        # Mock document service
        with patch("app.api.routes.query.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_chunks = [
                {"id": "chunk-1", "content": "Chunk 1", "chunk_index": 0},
                {"id": "chunk-2", "content": "Chunk 2", "chunk_index": 1},
            ]
            mock_service.get_document_chunks.return_value = mock_chunks
            mock_get_service.return_value = mock_service

            # Test getting chunks for existing document
            response = sync_client.get(f"/api/documents/{document_id}/chunks")

            # Verify response
            assert response.status_code == 200
            response_data = response.json()
            assert "chunks" in response_data
            assert len(response_data["chunks"]) == 2
            assert response_data["chunks"][0]["content"] == "Chunk 1"
            assert response_data["chunks"][1]["content"] == "Chunk 2"

            # Verify service was called
            mock_service.get_document_chunks.assert_called_once_with(document_id)

    @pytest.mark.asyncio
    async def test_get_document_chunks_endpoint_empty(self, sync_client):
        """Test the GET /documents/{id}/chunks endpoint with no chunks."""
        document_id = "non-existent-id"

        # Mock document service
        with patch("app.api.routes.query.get_document_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.get_document_chunks.return_value = []
            mock_get_service.return_value = mock_service

            # Test getting chunks for non-existent document
            response = sync_client.get(f"/api/documents/{document_id}/chunks")
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data["chunks"]) == 0
