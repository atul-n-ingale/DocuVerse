"""
Global pytest configuration and fixtures for DocuVerse backend tests.
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["PINECONE_ENVIRONMENT"] = "test-env"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/docuverse_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_pdf_file(temp_dir: str) -> str:
    """Create a sample PDF file for testing."""
    pdf_path = os.path.join(temp_dir, "sample.pdf")
    # Create a minimal PDF file content
    with open(pdf_path, "w") as f:
        f.write("Sample PDF content for testing")
    return pdf_path


@pytest.fixture
def sample_docx_file(temp_dir: str) -> str:
    """Create a sample DOCX file for testing."""
    docx_path = os.path.join(temp_dir, "sample.docx")
    with open(docx_path, "w") as f:
        f.write("Sample DOCX content for testing")
    return docx_path


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3] * 512)]  # Mock embedding vector
    mock_client.embeddings.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_pinecone_index() -> MagicMock:
    """Mock Pinecone index for testing."""
    mock_index = MagicMock()
    mock_index.upsert.return_value = {"upserted_count": 1}
    mock_index.query.return_value = MagicMock(
        matches=[
            MagicMock(id="test-doc-1", score=0.95, metadata={"content": "Test content", "document_id": "test-doc-1"})
        ]
    )
    return mock_index


@pytest.fixture
def mock_mongodb_client() -> MagicMock:
    """Mock MongoDB client for testing."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_client.get_default_database.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find_one.return_value = None
    mock_collection.insert_one.return_value = MagicMock(inserted_id="test-id")

    return mock_client


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    from main import app

    return app


@pytest.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sync_client(app) -> TestClient:
    """Create synchronous HTTP client for testing."""
    return TestClient(app)


@pytest.fixture
def mock_websocket_manager() -> MagicMock:
    """Mock WebSocket manager for testing."""
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = MagicMock()
    mock_manager.send_personal_message = AsyncMock()
    mock_manager.broadcast = AsyncMock()
    mock_manager.send_progress_update = AsyncMock()
    mock_manager.send_processing_complete = AsyncMock()
    mock_manager.send_error = AsyncMock()
    return mock_manager


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document data for testing."""
    return {
        "filename": "test_document.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "task_id": "test-task-123",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_query_request() -> dict:
    """Sample query request data for testing."""
    return {"query": "What is the main topic of the document?", "max_results": 5, "include_sources": True}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "external: mark test as requiring external services")
