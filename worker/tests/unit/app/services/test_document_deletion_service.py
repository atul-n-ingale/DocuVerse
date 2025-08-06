"""
Unit tests for document deletion service.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_deletion_service import delete_document_vectors


@pytest.mark.unit
class TestDocumentDeletionService:
    """Test cases for document deletion service functions."""

    def test_delete_document_vectors_success(self, mock_pinecone_client):
        """Test successful deletion of document vectors."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        # Mock Pinecone query response with some vectors
        mock_match1 = MagicMock()
        mock_match1.id = "vector-1"
        mock_match2 = MagicMock()
        mock_match2.id = "vector-2"

        mock_query_response = MagicMock()
        mock_query_response.matches = [mock_match1, mock_match2]

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.return_value = {
                "status": "success",
                "document_id": document_id,
                "deleted_vectors": 2,
                "error": None,
            }

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 2
            assert result["error"] is None

            # Verify CustomPineconeVectorStore was called correctly
            mock_vs_class.assert_called_once()
            mock_vector_store.delete_document.assert_called_once_with(
                document_id=document_id,
                progress_callback=mock_progress_manager.get_progress_callback.return_value,
            )

            # Verify ProgressManager was used correctly
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )
            mock_progress_manager.start_stage.assert_called_once_with("deletion")
            mock_progress_manager.complete_stage.assert_called_once_with("deletion")
            mock_progress_manager.send_final_progress_update.assert_called_once_with(
                status="completed", chunks=[]
            )

    def test_delete_document_vectors_no_vectors_found(self, mock_pinecone_client):
        """Test deletion when no vectors are found for the document."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.return_value = {
                "status": "success",
                "document_id": document_id,
                "deleted_vectors": 0,
                "error": None,
            }

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert result["error"] is None

            # Verify ProgressManager was used correctly
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )
            mock_progress_manager.start_stage.assert_called_once_with("deletion")
            mock_progress_manager.complete_stage.assert_called_once_with("deletion")

    def test_delete_document_vectors_large_batch(self, mock_pinecone_client):
        """Test deletion with large number of vectors."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.return_value = {
                "status": "success",
                "document_id": document_id,
                "deleted_vectors": 500,
                "error": None,
            }

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 500
            assert result["error"] is None

            # Verify ProgressManager was used correctly
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )

    def test_delete_document_vectors_missing_pinecone_config(self):
        """Test deletion when Pinecone API key is missing."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with patch("app.services.document_deletion_service.PINECONE_API_KEY", ""):
            result = delete_document_vectors(document_id, task_id)

            assert result["status"] == "error"
            assert "PINECONE_API_KEY is not configured" in result["error"]

    def test_delete_document_vectors_missing_index_config(self):
        """Test deletion when Pinecone index is missing."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with patch("app.services.document_deletion_service.PINECONE_INDEX", ""):
            result = delete_document_vectors(document_id, task_id)

            assert result["status"] == "error"
            assert "PINECONE_INDEX is not configured" in result["error"]

    def test_delete_document_vectors_pinecone_error(self, mock_pinecone_client):
        """Test deletion when Pinecone operations fail."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store to raise an error
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.side_effect = Exception("Pinecone error")

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            assert result["status"] == "error"
            assert "Pinecone error" in result["error"]

            # Verify ProgressManager was used for error reporting
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )

    def test_delete_document_vectors_query_error(self, mock_pinecone_client):
        """Test deletion when query operation fails."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store to raise an error during query
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.side_effect = Exception("Query failed")

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            assert result["status"] == "error"
            assert "Query failed" in result["error"]

            # Verify ProgressManager was used for error reporting
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )

    def test_delete_document_vectors_deletion_error(self, mock_pinecone_client):
        """Test deletion when vector deletion operation fails."""
        document_id = "test-doc-123"
        task_id = "test-task-id"

        with (
            patch(
                "app.services.document_deletion_service.CustomPineconeVectorStore"
            ) as mock_vs_class,
            patch(
                "app.services.document_deletion_service.ProgressManager"
            ) as mock_pm_class,
        ):
            # Mock vector store to return error status
            mock_vector_store = MagicMock()
            mock_vs_class.return_value = mock_vector_store
            mock_vector_store.delete_document.return_value = {
                "status": "error",
                "document_id": document_id,
                "deleted_vectors": 0,
                "error": "Deletion failed",
            }

            # Mock progress manager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            result = delete_document_vectors(document_id, task_id)

            assert result["status"] == "error"
            assert result["error"] == "Deletion failed"

            # Verify ProgressManager was used for error reporting
            mock_pm_class.assert_called_once_with(
                backend_url="http://localhost:8000",
                document_id=document_id,
                task_id=task_id,
                operation_type="deletion",
            )
            mock_progress_manager.send_final_progress_update.assert_called_with(
                status="failed", error="Deletion failed"
            )
