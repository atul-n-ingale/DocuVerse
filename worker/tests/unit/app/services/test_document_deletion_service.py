"""
Unit tests for document deletion service.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_deletion_service import (
    delete_document_vectors,
    report_deletion_status_to_backend,
)


@pytest.mark.unit
class TestDocumentDeletionService:
    """Test cases for document deletion service functions."""

    def test_delete_document_vectors_success(self, mock_pinecone_client):
        """Test successful deletion of document vectors."""
        document_id = "test-doc-123"

        # Mock Pinecone query response with some vectors
        mock_match1 = MagicMock()
        mock_match1.id = "vector-1"
        mock_match2 = MagicMock()
        mock_match2.id = "vector-2"

        mock_query_response = MagicMock()
        mock_query_response.matches = [mock_match1, mock_match2]

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.return_value.query.return_value = (
                mock_query_response
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 2
            assert result["error"] is None

            # Verify Pinecone was called correctly
            mock_pinecone_class.assert_called_once()
            mock_pinecone_client.Index.assert_called_once()

            # Verify query was called with correct parameters
            mock_index = mock_pinecone_client.Index.return_value
            mock_index.query.assert_called_once()
            call_args = mock_index.query.call_args
            assert call_args[1]["filter"] == {"document_id": {"$eq": document_id}}
            assert call_args[1]["top_k"] == 10000

            # Verify deletion was called
            assert mock_index.delete.call_count == 1
            delete_call_args = mock_index.delete.call_args
            assert delete_call_args[1]["ids"] == ["vector-1", "vector-2"]

            # Verify status reporting was called
            assert mock_report.call_count == 3  # deleting, progress, deletion_completed

    def test_delete_document_vectors_no_vectors_found(self, mock_pinecone_client):
        """Test deletion when no vectors are found for the document."""
        document_id = "test-doc-123"

        # Mock empty query response
        mock_query_response = MagicMock()
        mock_query_response.matches = []

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.return_value.query.return_value = (
                mock_query_response
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert result["error"] is None

            # Verify no deletion was called
            mock_index = mock_pinecone_client.Index.return_value
            mock_index.delete.assert_not_called()

            # Verify status reporting was called
            assert mock_report.call_count == 2  # deleting, deletion_completed

    def test_delete_document_vectors_large_batch(self, mock_pinecone_client):
        """Test deletion with large number of vectors requiring batching."""
        document_id = "test-doc-123"

        # Create 250 mock matches (will require 3 batches of 100)
        mock_matches = []
        for i in range(250):
            mock_match = MagicMock()
            mock_match.id = f"vector-{i}"
            mock_matches.append(mock_match)

        mock_query_response = MagicMock()
        mock_query_response.matches = mock_matches

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.return_value.query.return_value = (
                mock_query_response
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "success"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 250
            assert result["error"] is None

            # Verify deletion was called 3 times (batches of 100, 100, 50)
            mock_index = mock_pinecone_client.Index.return_value
            assert mock_index.delete.call_count == 3

            # Verify status reporting was called for progress updates
            assert (
                mock_report.call_count >= 3
            )  # deleting, progress updates, deletion_completed

    def test_delete_document_vectors_missing_pinecone_config(self):
        """Test deletion with missing Pinecone configuration."""
        document_id = "test-doc-123"

        with (
            patch("app.services.document_deletion_service.PINECONE_API_KEY", None),
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "error"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert "PINECONE_API_KEY is not configured" in result["error"]

            # Verify error was reported
            mock_report.assert_called_with(
                document_id, "deletion_failed", 0, error=result["error"]
            )

    def test_delete_document_vectors_missing_index_config(self):
        """Test deletion with missing Pinecone index configuration."""
        document_id = "test-doc-123"

        with (
            patch("app.services.document_deletion_service.PINECONE_INDEX", None),
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "error"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert "PINECONE_INDEX is not configured" in result["error"]

            # Verify error was reported
            mock_report.assert_called_with(
                document_id, "deletion_failed", 0, error=result["error"]
            )

    def test_delete_document_vectors_pinecone_error(self, mock_pinecone_client):
        """Test deletion when Pinecone operations fail."""
        document_id = "test-doc-123"

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.side_effect = Exception(
                "Pinecone connection error"
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "error"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert "Pinecone connection error" in result["error"]

            # Verify error was reported
            mock_report.assert_called_with(
                document_id, "deletion_failed", 0, error=result["error"]
            )

    def test_delete_document_vectors_query_error(self, mock_pinecone_client):
        """Test deletion when Pinecone query fails."""
        document_id = "test-doc-123"

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.return_value.query.side_effect = Exception(
                "Query failed"
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "error"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert "Query failed" in result["error"]

            # Verify error was reported
            mock_report.assert_called_with(
                document_id, "deletion_failed", 0, error=result["error"]
            )

    def test_delete_document_vectors_deletion_error(self, mock_pinecone_client):
        """Test deletion when vector deletion fails."""
        document_id = "test-doc-123"

        # Mock query response with some vectors
        mock_match = MagicMock()
        mock_match.id = "vector-1"
        mock_query_response = MagicMock()
        mock_query_response.matches = [mock_match]

        with (
            patch(
                "app.services.document_deletion_service.pinecone.Pinecone"
            ) as mock_pinecone_class,
            patch(
                "app.services.document_deletion_service.report_deletion_status_to_backend"
            ) as mock_report,
        ):
            mock_pinecone_class.return_value = mock_pinecone_client
            mock_pinecone_client.Index.return_value.query.return_value = (
                mock_query_response
            )
            mock_pinecone_client.Index.return_value.delete.side_effect = Exception(
                "Deletion failed"
            )

            result = delete_document_vectors(document_id)

            # Assertions
            assert result["status"] == "error"
            assert result["document_id"] == document_id
            assert result["deleted_vectors"] == 0
            assert "Deletion failed" in result["error"]

            # Verify error was reported
            mock_report.assert_called_with(
                document_id, "deletion_failed", 0, error=result["error"]
            )

    def test_report_deletion_status_to_backend_success(self, mock_requests_post):
        """Test successful status reporting to backend."""
        document_id = "test-doc-123"

        with patch("app.services.document_deletion_service.requests.post") as mock_post:
            mock_post.return_value = mock_requests_post

            # Should not raise an exception
            report_deletion_status_to_backend(document_id, "deleting", 50)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["task_id"] == f"delete_{document_id}"
            assert call_args[1]["json"]["document_id"] == document_id
            assert call_args[1]["json"]["status"] == "deleting"
            assert call_args[1]["json"]["chunks"] == []
            assert call_args[1]["json"]["error"] is None

    def test_report_deletion_status_to_backend_with_error(self, mock_requests_post):
        """Test status reporting with error message."""
        document_id = "test-doc-123"
        error_message = "Test deletion error"

        with patch("app.services.document_deletion_service.requests.post") as mock_post:
            mock_post.return_value = mock_requests_post

            report_deletion_status_to_backend(
                document_id, "deletion_failed", 0, error=error_message
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[1]["json"]["error"] == error_message

    def test_report_deletion_status_to_backend_http_error(self):
        """Test status reporting when backend returns HTTP error."""
        document_id = "test-doc-123"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("app.services.document_deletion_service.requests.post") as mock_post:
            mock_post.return_value = mock_response

            # Should not raise an exception, just log the error
            report_deletion_status_to_backend(document_id, "deleting", 50)

            mock_post.assert_called_once()

    def test_report_deletion_status_to_backend_network_error(self):
        """Test status reporting when network request fails."""
        document_id = "test-doc-123"

        with patch("app.services.document_deletion_service.requests.post") as mock_post:
            mock_post.side_effect = Exception("Network error")

            # Should not raise an exception, just log the error
            report_deletion_status_to_backend(document_id, "deleting", 50)

            mock_post.assert_called_once()

    def test_report_deletion_status_to_backend_timeout(self):
        """Test status reporting with timeout."""
        document_id = "test-doc-123"

        with patch("app.services.document_deletion_service.requests.post") as mock_post:
            mock_post.side_effect = Exception("Request timeout")

            # Should not raise an exception, just log the error
            report_deletion_status_to_backend(document_id, "deleting", 50)

            mock_post.assert_called_once()
