"""
Global pytest configuration and fixtures for DocuVerse worker tests.
"""

import os
import tempfile
from typing import Generator
from unittest.mock import MagicMock

import pytest

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["PINECONE_INDEX"] = "test-index"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/docuverse_worker_test"
os.environ["BACKEND_URL"] = "http://localhost:8000"


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_pdf_file(temp_dir: str) -> str:
    """Create a sample PDF file for testing."""
    pdf_path = os.path.join(temp_dir, "sample.pdf")
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
def sample_csv_file(temp_dir: str) -> str:
    """Create a sample CSV file for testing."""
    csv_path = os.path.join(temp_dir, "sample.csv")
    with open(csv_path, "w") as f:
        f.write("col1,col2,col3\nvalue1,value2,value3\n")
    return csv_path


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3] * 512)]
    mock_client.embeddings.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_pinecone_client() -> MagicMock:
    """Mock Pinecone client for testing."""
    mock_pc = MagicMock()
    mock_index = MagicMock()
    mock_index.upsert.return_value = {"upserted_count": 1}
    mock_pc.Index.return_value = mock_index
    return mock_pc


@pytest.fixture
def mock_mongodb_client() -> MagicMock:
    """Mock MongoDB client for testing."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_client.get_default_database.return_value = mock_db
    mock_db.document_workflows = mock_collection
    mock_collection.update_one.return_value = None

    return mock_client


@pytest.fixture
def mock_llama_index_readers() -> dict:
    """Mock LlamaIndex readers for testing."""
    mock_readers = {}

    # Mock PDFReader
    mock_pdf_reader = MagicMock()
    mock_pdf_reader.load_data.return_value = [MagicMock(text="Sample PDF content")]
    mock_readers["PDFReader"] = mock_pdf_reader

    # Mock DocxReader
    mock_docx_reader = MagicMock()
    mock_docx_reader.load_data.return_value = [MagicMock(text="Sample DOCX content")]
    mock_readers["DocxReader"] = mock_docx_reader

    # Mock CSVReader
    mock_csv_reader = MagicMock()
    mock_csv_reader.load_data.return_value = [
        MagicMock(text="col1,col2,col3\nvalue1,value2,value3")
    ]
    mock_readers["CSVReader"] = mock_csv_reader

    return mock_readers


@pytest.fixture
def mock_sentence_splitter() -> MagicMock:
    """Mock LlamaIndex SentenceSplitter for testing."""
    mock_splitter = MagicMock()
    mock_node = MagicMock()
    mock_node.get_content.return_value = "Sample chunk content"
    mock_splitter.get_nodes_from_documents.return_value = [mock_node]
    return mock_splitter


@pytest.fixture
def sample_document_data() -> dict:
    """Sample document processing data for testing."""
    return {
        "task_id": "test-task-123",
        "document_id": "test-doc-456",
        "file_path": "/tmp/test.pdf",
        "status": "processing",
        "chunks": [],
        "error": None,
    }


@pytest.fixture
def mock_requests_post() -> MagicMock:
    """Mock requests.post for testing backend communication."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "success"}'

    mock_post = MagicMock(return_value=mock_response)
    return mock_post


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "celery: mark test as requiring Celery")
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )
