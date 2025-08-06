"""
Unit tests for app.services.document_service module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest  # type: ignore

from app.models.document import Document, DocumentCreate, ProcessingStatus
from app.services.document_service import DocumentService, get_document_service


@pytest.mark.unit
class TestDocumentService:
    """Test cases for DocumentService class."""

    @pytest.fixture
    def mock_collection(self):
        """Mock database collection."""
        mock_collection = MagicMock()
        # Make database operations async
        mock_collection.insert_one = AsyncMock()
        mock_collection.find_one = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.delete_one = AsyncMock()
        mock_collection.delete_many = AsyncMock()
        mock_collection.find = MagicMock()
        mock_collection.insert_many = AsyncMock()
        return mock_collection

    @pytest.fixture
    def document_service(self, mock_collection):
        """Create DocumentService instance with mocked dependencies."""
        with patch("app.services.document_service.get_collection") as mock_get_collection:
            mock_get_collection.return_value = mock_collection
            service = DocumentService()
            service.documents_collection = mock_collection
            service.chunks_collection = mock_collection
            return service

    @pytest.fixture
    def sample_document_create(self):
        """Sample DocumentCreate data."""
        return DocumentCreate(filename="test.pdf", file_type="pdf", file_size=1024, task_id="test-task-123")

    @pytest.mark.asyncio
    async def test_create_document(self, document_service, sample_document_create, mock_collection):
        """Test document creation."""
        # Mock the database response
        mock_collection.insert_one.return_value = MagicMock(inserted_id="test-id")

        # Call the method
        result = await document_service.create_document(sample_document_create)

        # Assertions
        assert isinstance(result, Document)
        assert result.filename == "test.pdf"
        assert result.file_type == "pdf"
        mock_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_found(self, document_service, mock_collection):
        """Test getting an existing document."""
        # Mock the database response
        mock_collection.find_one.return_value = {
            "_id": "test-id",
            "filename": "test.pdf",
            "file_type": "pdf",
            "file_size": 1024,
            "task_id": "test-task-123",
            "status": "pending",
        }

        # Call the method
        result = await document_service.get_document("test-id")

        # Assertions
        assert isinstance(result, Document)
        assert result.id == "test-id"
        assert result.filename == "test.pdf"
        mock_collection.find_one.assert_called_once_with({"_id": "test-id"})

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, document_service, mock_collection):
        """Test getting a non-existent document."""
        # Mock the database response
        mock_collection.find_one.return_value = None

        # Call the method
        result = await document_service.get_document("non-existent-id")

        # Assertions
        assert result is None
        mock_collection.find_one.assert_called_once_with({"_id": "non-existent-id"})

    @pytest.mark.asyncio
    async def test_update_document_status(self, document_service, mock_collection):
        """Test updating document status."""
        # Call the method
        await document_service.update_document_status("test-id", ProcessingStatus.COMPLETED, chunks_count=5)

        # Assertions
        mock_collection.update_one.assert_called_once_with(
            {"_id": "test-id"}, {"$set": {"status": ProcessingStatus.COMPLETED, "chunks_count": 5}}
        )

    @pytest.mark.asyncio
    async def test_get_all_documents(self, document_service, mock_collection):
        """Test getting all documents."""
        # Mock the database response
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {
                "_id": "test-id-1",
                "filename": "test1.pdf",
                "file_type": "pdf",
                "file_size": 1024,
                "task_id": "task-1",
                "status": "pending",
            },
            {
                "_id": "test-id-2",
                "filename": "test2.pdf",
                "file_type": "pdf",
                "file_size": 2048,
                "task_id": "task-2",
                "status": "completed",
            },
        ]
        mock_collection.find.return_value = mock_cursor

        # Call the method
        result = await document_service.get_all_documents()

        # Assertions
        assert len(result) == 2
        assert all(isinstance(doc, Document) for doc in result)
        assert result[0].id == "test-id-1"
        assert result[1].id == "test-id-2"

    @pytest.mark.asyncio
    async def test_delete_document(self, document_service, mock_collection):
        """Test deleting a document."""
        # Call the method
        await document_service.delete_document("test-id")

        # Assertions
        assert mock_collection.delete_one.call_count == 1
        assert mock_collection.delete_many.call_count == 1
        mock_collection.delete_one.assert_called_with({"_id": "test-id"})
        mock_collection.delete_many.assert_called_with({"document_id": "test-id"})

    @pytest.mark.asyncio
    async def test_save_chunks(self, document_service, mock_collection):
        """Test saving document chunks to the chunks collection."""
        chunks = [
            {"content": "chunk1"},
            {"content": "chunk2"},
        ]
        document_id = "doc-123"

        await document_service.save_chunks(document_id, chunks)

        # Each chunk should have _id and document_id set
        for chunk in chunks:
            assert "_id" in chunk
            assert chunk["document_id"] == document_id
        mock_collection.insert_many.assert_called_once_with(chunks)

    @pytest.mark.asyncio
    async def test_get_document_chunks(self, document_service, mock_collection):
        """Test retrieving all chunks for a document."""
        document_id = "doc-123"
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {"_id": "chunk-1", "document_id": document_id, "content": "chunk1"},
            {"_id": "chunk-2", "document_id": document_id, "content": "chunk2"},
        ]
        mock_collection.find.return_value = mock_cursor

        result = await document_service.get_document_chunks(document_id)
        assert len(result) == 2
        assert result[0]["id"] == "chunk-1"
        assert result[1]["id"] == "chunk-2"
        assert result[0]["content"] == "chunk1"
        assert result[1]["content"] == "chunk2"
        mock_collection.find.assert_called_once_with({"document_id": document_id})

    @pytest.mark.asyncio
    async def test_mark_document_deleting(self, document_service, mock_collection):
        """Test marking a document as deleting."""
        document_id = "doc-123"
        with patch.object(document_service, "update_document_status", new_callable=AsyncMock) as mock_update:
            await document_service.mark_document_deleting(document_id)
            mock_update.assert_called_once_with(document_id, ProcessingStatus.DELETING)

    @pytest.mark.asyncio
    async def test_mark_document_delete_error(self, document_service, mock_collection):
        """Test marking a document deletion as failed with error message."""
        document_id = "doc-123"
        error_message = "Delete failed"
        with patch.object(document_service, "update_document_status", new_callable=AsyncMock) as mock_update:
            await document_service.mark_document_delete_error(document_id, error_message)
            mock_update.assert_called_once_with(document_id, ProcessingStatus.DELETE_ERROR, error_message=error_message)


@pytest.mark.unit
@patch("app.services.document_service.get_collection")
def test_get_document_service(mock_get_collection):
    """Test the global document service getter."""
    # Mock the database collection
    mock_collection = MagicMock()
    mock_get_collection.return_value = mock_collection

    # Clear any existing instance
    import app.services.document_service

    app.services.document_service._document_service = None

    service1 = get_document_service()
    service2 = get_document_service()

    # Should return the same instance (singleton pattern)
    assert service1 is service2
    assert isinstance(service1, DocumentService)
