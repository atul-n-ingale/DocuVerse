"""
Unit tests for app.services.document_processor_service module.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_processor_service import (
    process_document,
    report_status_to_backend,
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

    def test_report_status_to_backend_success(self, mock_requests_post):
        """Test successful status reporting to backend."""
        with patch(
            "app.services.document_processor_service.requests.post"
        ) as mock_post:
            mock_post.return_value = mock_requests_post

            # Should not raise an exception
            report_status_to_backend("task-123", "doc-456", "completed", 5)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["task_id"] == "task-123"
            assert call_args[1]["json"]["document_id"] == "doc-456"
            assert call_args[1]["json"]["status"] == "completed"
            assert call_args[1]["json"]["chunks"] == 5

    def test_report_status_to_backend_with_error(self, mock_requests_post):
        """Test status reporting with error message."""
        with patch(
            "app.services.document_processor_service.requests.post"
        ) as mock_post:
            mock_post.return_value = mock_requests_post

            report_status_to_backend(
                "task-123", "doc-456", "failed", [], error="Test error"
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["error"] == "Test error"

    @patch("app.services.document_processor_service.extract_text")
    @patch("app.services.document_processor_service.upsert_pinecone")
    @patch("app.services.document_processor_service.save_workflow_state")
    @patch("app.services.document_processor_service.report_status_to_backend")
    def test_process_document_success(
        self,
        mock_report_status,
        mock_save_state,
        mock_upsert,
        mock_extract_text,
        mock_openai_client,
        mock_sentence_splitter,
        sample_document_data,
    ):
        """Test successful document processing."""
        # Setup mocks
        mock_extract_text.return_value = "Sample document content"

        with (
            patch(
                "app.services.document_processor_service.OpenAI"
            ) as mock_openai_class,
            patch(
                "app.services.document_processor_service.SentenceSplitter"
            ) as mock_splitter_class,
        ):

            mock_openai_class.return_value = mock_openai_client
            mock_splitter_class.return_value = mock_sentence_splitter

            # Call the function
            result = process_document(
                sample_document_data["task_id"],
                sample_document_data["file_path"],
                sample_document_data["document_id"],
            )

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == sample_document_data["document_id"]
            assert "chunks" in result

            # Verify all steps were called
            mock_extract_text.assert_called_once()
            mock_upsert.assert_called_once()
            mock_save_state.assert_called()
            mock_report_status.assert_called()

    @patch("app.services.document_processor_service.extract_text")
    @patch("app.services.document_processor_service.report_status_to_backend")
    def test_process_document_failure(
        self, mock_report_status, mock_extract_text, sample_document_data
    ):
        """Test document processing with failure."""
        # Setup mock to raise exception
        mock_extract_text.side_effect = Exception("Test extraction error")

        # Call the function
        result = process_document(
            sample_document_data["task_id"],
            sample_document_data["file_path"],
            sample_document_data["document_id"],
        )

        # Assertions
        assert result["status"] == "error"
        assert "Test extraction error" in result["error"]

        # Verify error reporting was called
        mock_report_status.assert_called_with(
            sample_document_data["task_id"],
            sample_document_data["document_id"],
            "failed",
            [],
            error="Test extraction error",
        )
