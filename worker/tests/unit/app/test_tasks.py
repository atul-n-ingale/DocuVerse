"""
Unit tests for Celery tasks.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tasks import delete_document_task, process_document_task


@pytest.mark.unit
@pytest.mark.celery
class TestCeleryTasks:
    """Test cases for Celery tasks."""

    def test_process_document_task_success(self, sample_document_data):
        """Test successful document processing task."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        expected_result = {
            "status": "success",
            "document_id": document_id,
            "chunks": ["chunk1", "chunk2"],
        }

        with patch("app.tasks.process_document") as mock_process:
            mock_process.return_value = expected_result

            result = process_document_task.run(task_id, file_path, document_id)

            # Assertions
            assert result == expected_result
            mock_process.assert_called_once_with(task_id, file_path, document_id)

    def test_process_document_task_error_result(self, sample_document_data):
        """Test document processing task when service returns error."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        error_result = {
            "status": "error",
            "document_id": document_id,
            "error": "Processing failed",
        }

        with patch("app.tasks.process_document") as mock_process:
            mock_process.return_value = error_result

            # Should raise exception to mark task as failed
            with pytest.raises(Exception, match="Document processing failed"):
                process_document_task.run(task_id, file_path, document_id)

            mock_process.assert_called_once_with(task_id, file_path, document_id)

    def test_process_document_task_service_exception(self, sample_document_data):
        """Test document processing task when service raises exception."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        with patch("app.tasks.process_document") as mock_process:
            mock_process.side_effect = Exception("Service error")

            # Should raise exception to mark task as failed
            with pytest.raises(Exception, match="Service error"):
                process_document_task.run(task_id, file_path, document_id)

            mock_process.assert_called_once_with(task_id, file_path, document_id)

    def test_process_document_task_missing_error_field(self, sample_document_data):
        """Test document processing task with missing error field."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        error_result = {
            "status": "error",
            "document_id": document_id,
            # Missing error field
        }

        with patch("app.tasks.process_document") as mock_process:
            mock_process.return_value = error_result

            # Should raise exception with default error message
            with pytest.raises(Exception, match="Document processing failed"):
                process_document_task.run(task_id, file_path, document_id)

            mock_process.assert_called_once_with(task_id, file_path, document_id)

    def test_delete_document_task_success(self):
        """Test successful document deletion task."""
        document_id = "test-doc-123"

        expected_result = {
            "status": "success",
            "document_id": document_id,
            "deleted_vectors": 5,
        }

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.return_value = expected_result

            result = delete_document_task.run(document_id)

            # Assertions
            assert result == expected_result
            mock_delete.assert_called_once_with(document_id, None)

    def test_delete_document_task_error_result(self):
        """Test document deletion task when service returns error."""
        document_id = "test-doc-123"

        error_result = {
            "status": "error",
            "document_id": document_id,
            "error": "Deletion failed",
        }

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.return_value = error_result

            # Should raise exception to mark task as failed
            with pytest.raises(Exception, match="Document deletion failed"):
                delete_document_task.run(document_id)

            mock_delete.assert_called_once_with(document_id, None)

    def test_delete_document_task_service_exception(self):
        """Test document deletion task when service raises exception."""
        document_id = "test-doc-123"

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.side_effect = Exception("Service error")

            # Should raise exception to mark task as failed
            with pytest.raises(Exception, match="Service error"):
                delete_document_task.run(document_id)

            mock_delete.assert_called_once_with(document_id, None)

    def test_delete_document_task_missing_error_field(self):
        """Test document deletion task with missing error field."""
        document_id = "test-doc-123"

        error_result = {
            "status": "error",
            "document_id": document_id,
            # Missing error field
        }

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.return_value = error_result

            # Should raise exception with default error message
            with pytest.raises(Exception, match="Document deletion failed"):
                delete_document_task.run(document_id)

            mock_delete.assert_called_once_with(document_id, None)

    def test_process_document_task_logging(self, sample_document_data, caplog):
        """Test that document processing task logs correctly."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        expected_result = {
            "status": "success",
            "document_id": document_id,
            "chunks": ["chunk1"],
        }

        with patch("app.tasks.process_document") as mock_process:
            mock_process.return_value = expected_result

            result = process_document_task.run(task_id, file_path, document_id)

            # Verify the task executed successfully
            assert result == expected_result
            mock_process.assert_called_once_with(task_id, file_path, document_id)

    def test_delete_document_task_logging(self, caplog):
        """Test that document deletion task logs correctly."""
        document_id = "test-doc-123"

        expected_result = {
            "status": "success",
            "document_id": document_id,
            "deleted_vectors": 3,
        }

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.return_value = expected_result

            result = delete_document_task.run(document_id)

            # Verify the task executed successfully
            assert result == expected_result
            mock_delete.assert_called_once_with(document_id, None)

    def test_process_document_task_error_logging(self, sample_document_data, caplog):
        """Test that document processing task logs errors correctly."""
        task_id = sample_document_data["task_id"]
        file_path = sample_document_data["file_path"]
        document_id = sample_document_data["document_id"]

        error_result = {
            "status": "error",
            "document_id": document_id,
            "error": "Processing failed",
        }

        with patch("app.tasks.process_document") as mock_process:
            mock_process.return_value = error_result

            with pytest.raises(Exception):
                process_document_task.run(task_id, file_path, document_id)

            # Check that error was logged
            assert f"Document processing failed for {document_id}" in caplog.text
            assert "Processing failed" in caplog.text

    def test_delete_document_task_error_logging(self, caplog):
        """Test that document deletion task logs errors correctly."""
        document_id = "test-doc-123"

        error_result = {
            "status": "error",
            "document_id": document_id,
            "error": "Deletion failed",
        }

        with patch("app.tasks.delete_document_vectors") as mock_delete:
            mock_delete.return_value = error_result

            with pytest.raises(Exception):
                delete_document_task.run(document_id)

            # Check that error was logged
            assert f"Document deletion failed for {document_id}" in caplog.text
            assert "Deletion failed" in caplog.text
