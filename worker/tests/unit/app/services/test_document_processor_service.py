"""
Unit tests for app.services.document_processor_service module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.config import BACKEND_URL
from app.services.document_processor_service import (
    process_document,
    save_workflow_state,
    upsert_pinecone,
)


@pytest.mark.unit
class TestDocumentProcessorService:
    """Test cases for document processor service functions."""

    def test_upsert_pinecone_success(self, mock_pinecone_client):
        """Test successful vector upsert to Pinecone."""
        document_id = "test-doc-123"
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        chunks = ["chunk1", "chunk2"]

        with patch(
            "app.services.document_processor_service.pinecone.Pinecone"
        ) as mock_pinecone_class:
            mock_pinecone_class.return_value = mock_pinecone_client

            # Should not raise an exception
            upsert_pinecone(document_id, embeddings, chunks)

            mock_pinecone_class.assert_called_once()
            mock_pinecone_client.Index.assert_called_once()

    def test_save_workflow_state(self, mock_mongodb_client):
        """Test saving workflow state to MongoDB."""
        document_id = "test-doc-123"
        state = {"status": "completed", "chunks": 5}

        with patch(
            "app.services.document_processor_service.pymongo.MongoClient"
        ) as mock_mongo_class:
            mock_mongo_class.return_value = mock_mongodb_client

            save_workflow_state(document_id, state)

            mock_mongo_class.assert_called_once()
            mock_mongodb_client.get_default_database.assert_called_once()

    def test_process_document_success_with_progress_manager(self, mock_requests_post):
        """Test successful document processing with ProgressManager."""
        with (
            patch(
                "app.services.document_processor_service.ProgressManager"
            ) as mock_pm_class,
            patch(
                "app.services.document_ingestor.DocumentIngestor"
            ) as mock_ingestor_class,
        ):
            # Mock ProgressManager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            # Mock DocumentIngestor
            mock_ingestor = MagicMock()
            mock_ingestor_class.return_value = mock_ingestor
            mock_ingestor.ingest.return_value = 5  # 5 chunks

            # Test the function
            result = process_document("task-123", "/path/to/file.pdf", "doc-456")

            # Verify result
            assert result["status"] == "success"
            assert result["document_id"] == "doc-456"
            assert result["chunks"] == 5

            # Verify ProgressManager was used
            mock_pm_class.assert_called_once_with(
                backend_url=BACKEND_URL,
                document_id="doc-456",
                task_id="task-123",
                operation_type="processing",
            )
            mock_progress_manager.report_status_to_backend.assert_called_once_with(
                "processing"
            )

            # Verify DocumentIngestor was used
            mock_ingestor_class.assert_called_once_with(
                "doc-456", "/path/to/file.pdf", mock_progress_manager
            )
            mock_ingestor.ingest.assert_called_once()

    def test_process_document_failure_with_progress_manager(self, mock_requests_post):
        """Test document processing failure with ProgressManager."""
        with (
            patch(
                "app.services.document_processor_service.ProgressManager"
            ) as mock_pm_class,
            patch(
                "app.services.document_ingestor.DocumentIngestor"
            ) as mock_ingestor_class,
        ):
            # Mock ProgressManager
            mock_progress_manager = MagicMock()
            mock_pm_class.return_value = mock_progress_manager

            # Mock DocumentIngestor to raise an exception
            mock_ingestor = MagicMock()
            mock_ingestor_class.return_value = mock_ingestor
            mock_ingestor.ingest.side_effect = Exception("Processing failed")

            # Test the function
            result = process_document("task-123", "/path/to/file.pdf", "doc-456")

            # Verify result
            assert result["status"] == "error"
            assert result["document_id"] == "doc-456"
            assert "Processing failed" in result["error"]

            # Verify ProgressManager was used
            mock_pm_class.assert_called_once_with(
                backend_url=BACKEND_URL,
                document_id="doc-456",
                task_id="task-123",
                operation_type="processing",
            )
            mock_progress_manager.report_status_to_backend.assert_called_once_with(
                "processing"
            )

    @patch("app.services.document_processor_service.ProgressManager")
    def test_process_document_success(
        self,
        mock_progress_manager_class,
        mock_openai_client,
        mock_sentence_splitter,
        sample_document_data,
    ):
        """Test successful document processing."""
        # Setup mocks
        mock_progress_manager = MagicMock()
        mock_progress_manager_class.return_value = mock_progress_manager

        # Mock DocumentIngestor
        with patch(
            "app.services.document_ingestor.DocumentIngestor"
        ) as mock_ingestor_class:
            mock_ingestor = MagicMock()
            mock_ingestor_class.return_value = mock_ingestor
            mock_ingestor.ingest.return_value = 5  # 5 chunks

            # Test the function
            result = process_document("task-123", "/path/to/file.pdf", "doc-456")

            # Verify result
            assert result["status"] == "success"
            assert result["document_id"] == "doc-456"
            assert result["chunks"] == 5

            # Verify ProgressManager was used
            mock_progress_manager_class.assert_called_once()
            mock_progress_manager.report_status_to_backend.assert_called_once_with(
                "processing"
            )

    @patch("app.services.document_processor_service.ProgressManager")
    def test_process_document_failure(
        self, mock_progress_manager_class, sample_document_data
    ):
        """Test document processing failure."""
        # Setup mocks
        mock_progress_manager = MagicMock()
        mock_progress_manager_class.return_value = mock_progress_manager

        # Mock DocumentIngestor to raise an exception
        with patch(
            "app.services.document_ingestor.DocumentIngestor"
        ) as mock_ingestor_class:
            mock_ingestor = MagicMock()
            mock_ingestor_class.return_value = mock_ingestor
            mock_ingestor.ingest.side_effect = Exception("Processing failed")

            # Test the function
            result = process_document("task-123", "/path/to/file.pdf", "doc-456")

            # Verify result
            assert result["status"] == "error"
            assert result["document_id"] == "doc-456"
            assert "Processing failed" in result["error"]

            # Verify ProgressManager was used
            mock_progress_manager_class.assert_called_once()
            mock_progress_manager.report_status_to_backend.assert_called_once_with(
                "processing"
            )
