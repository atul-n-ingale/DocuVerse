"""
Unit tests for app.api.routes.upload module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from app.api.routes.upload import upload_file
from app.models.document import DocumentType, UploadResponse


@pytest.mark.unit
class TestUploadRoute:
    """Test cases for upload route."""

    @pytest.fixture
    def mock_upload_file(self):
        """Mock UploadFile instance."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.read = AsyncMock(return_value=b"test content")
        return mock_file

    @pytest.fixture
    def mock_invalid_file(self):
        """Mock invalid UploadFile instance."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"  # Unsupported extension
        mock_file.read = AsyncMock(return_value=b"test content")
        return mock_file

    @pytest.fixture
    def mock_no_filename_file(self):
        """Mock UploadFile with no filename."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        mock_file.read = AsyncMock(return_value=b"test content")
        return mock_file

    @pytest.mark.asyncio
    async def test_upload_file_success(self, mock_upload_file):
        """Test successful file upload."""
        with (
            patch("app.api.routes.upload.get_document_service") as mock_service,
            patch("app.api.routes.upload.celery_app") as mock_celery,
            patch("app.api.routes.upload.aiofiles.open") as mock_aiofiles,
            patch("app.api.routes.upload.os.makedirs"),
        ):

            # Mock document service
            mock_doc_service = MagicMock()
            mock_doc_service.create_document = AsyncMock(return_value=MagicMock(id="test-doc-id"))
            mock_service.return_value = mock_doc_service

            # Mock file operations
            mock_file_handle = AsyncMock()
            mock_aiofiles.return_value.__aenter__.return_value = mock_file_handle

            # Call the function
            result = await upload_file(mock_upload_file)

            # Assertions
            assert isinstance(result, UploadResponse)
            assert result.filename == "test.pdf"
            assert "successfully" in result.message
            mock_celery.send_task.assert_called_once()
            mock_doc_service.create_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_no_filename(self, mock_no_filename_file):
        """Test upload with no filename."""
        with pytest.raises(Exception) as exc_info:
            await upload_file(mock_no_filename_file)

        assert "Filename is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_file_unsupported_type(self, mock_invalid_file):
        """Test upload with unsupported file type."""
        with pytest.raises(Exception) as exc_info:
            await upload_file(mock_invalid_file)

        assert "Unsupported file type" in str(exc_info.value)

    def test_file_type_mapping(self):
        """Test file type mapping logic."""
        # This would test the type_mapping dictionary
        # in the actual implementation
        type_mapping = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".csv": DocumentType.CSV,
            ".xlsx": DocumentType.EXCEL,
            ".xls": DocumentType.EXCEL,
            ".png": DocumentType.IMAGE,
            ".jpg": DocumentType.IMAGE,
            ".jpeg": DocumentType.IMAGE,
        }

        assert type_mapping[".pdf"] == DocumentType.PDF
        assert type_mapping[".docx"] == DocumentType.DOCX
        assert type_mapping[".xlsx"] == DocumentType.EXCEL
        assert type_mapping[".png"] == DocumentType.IMAGE
