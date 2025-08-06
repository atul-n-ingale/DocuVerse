# DocuVerse Testing Guide

This guide covers the comprehensive testing framework for the DocuVerse project, including backend and worker components.

## Testing Architecture

The testing framework is organized into three main categories:

### 1. **Unit Tests** (`tests/unit/`)
- Test individual functions and classes in isolation
- Fast execution with mocked dependencies
- High coverage of business logic
- Located in `tests/unit/` with structure mirroring source code

### 2. **Integration Tests** (`tests/integration/`)
- Test component interactions and API endpoints
- Use real database connections (test databases)
- Test service integrations
- Located in `tests/integration/` with structure mirroring source code

### 3. **End-to-End Tests** (`tests/e2e/`)
- Test complete workflows from start to finish
- Use real external services or comprehensive mocks
- Test user scenarios and business processes
- Located in `tests/e2e/workflows/`

## Directory Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Global fixtures and configuration
│   ├── pytest.ini                    # Pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── core/
│   │       │   ├── __init__.py
│   │       │   ├── test_config.py
│   │       │   ├── test_database.py
│   │       │   └── test_websocket_manager.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── test_document_service.py
│   │       │   ├── test_embedding_service.py
│   │       │   └── test_vector_store.py
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   └── routes/
│   │       │       ├── __init__.py
│   │       │       ├── test_upload.py
│   │       │       ├── test_documents.py
│   │       │       ├── test_query.py
│   │       │       └── test_worker.py
│   │       └── models/
│   │           ├── __init__.py
│   │           └── test_document.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── test_document_service_integration.py
│   │       │   └── test_embedding_service_integration.py
│   │       └── api/
│   │           ├── __init__.py
│   │           ├── test_upload_integration.py
│   │           └── test_query_integration.py
│   └── e2e/
│       ├── __init__.py
│       └── workflows/
│           ├── __init__.py
│           ├── test_document_processing_workflow.py
│           └── test_query_workflow.py

worker/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Global fixtures and configuration
│   ├── pytest.ini                    # Pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   └── test_document_processor_service.py
│   │       └── test_tasks.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── app/
│   │       ├── __init__.py
│   │       └── services/
│   │           ├── __init__.py
│   │           └── test_document_processor_integration.py
│   └── e2e/
│       ├── __init__.py
│       └── workflows/
│           ├── __init__.py
│           └── test_document_processing_e2e.py
```

## Running Tests

### Basic Commands

```bash
# Run all tests
make test

# Run specific test types
make test-unit           # Unit tests only
make test-integration    # Integration tests only
make test-e2e           # End-to-end tests only

# Run tests for specific component
make test-backend       # Backend tests only
make test-worker        # Worker tests only

# Run fast tests (exclude slow tests)
make test-fast

# Run tests with coverage
make test-coverage
```

### Advanced Commands

```bash
# Run specific test file
make test-specific FILE=tests/unit/app/core/test_config.py

# Run tests with specific marker
make test-marker MARKER=unit

# Run tests matching keyword
make test-keyword KEYWORD=test_document

# Run only failed tests from last run
make test-failed

# Run tests with debugging
make test-debug

# Run tests in parallel
make test-parallel

# Watch mode for development
make test-watch
```

### Backend-Specific Commands

```bash
cd backend

# Run all backend tests
poetry run pytest

# Run specific test types
poetry run pytest tests/unit/ -m unit
poetry run pytest tests/integration/ -m integration
poetry run pytest tests/e2e/ -m e2e

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run async tests
poetry run pytest -m asyncio
```

### Worker-Specific Commands

```bash
cd worker

# Run all worker tests
poetry run pytest

# Run Celery-specific tests
poetry run pytest -m celery

# Run with coverage
poetry run pytest --cov=app --cov-report=html
```

## Test Markers

The following markers are available for organizing tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.database` - Tests requiring database
- `@pytest.mark.external` - Tests requiring external services
- `@pytest.mark.asyncio` - Async tests (backend)
- `@pytest.mark.celery` - Celery tests (worker)

## Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import MagicMock, patch

from app.services.document_service import DocumentService


@pytest.mark.unit
class TestDocumentService:
    """Test cases for DocumentService class."""

    @pytest.fixture
    def document_service(self):
        """Create DocumentService instance with mocked dependencies."""
        with patch('app.services.document_service.get_collection') as mock_get_collection:
            mock_get_collection.return_value = MagicMock()
            return DocumentService()

    @pytest.mark.asyncio
    async def test_create_document(self, document_service, sample_document_data):
        """Test document creation."""
        # Test implementation
        pass
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.integration
class TestUploadIntegration:
    """Integration tests for upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_workflow(self):
        """Test complete upload workflow."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test implementation
            pass
```

### E2E Test Example

```python
import pytest


@pytest.mark.e2e
@pytest.mark.slow
class TestDocumentProcessingWorkflow:
    """End-to-end tests for document processing workflow."""

    @pytest.mark.asyncio
    async def test_complete_document_processing(self):
        """Test complete document processing from upload to query."""
        # Test implementation
        pass
```

## Fixtures and Utilities

### Global Fixtures (conftest.py)

Common fixtures available across all tests:

- `temp_dir` - Temporary directory for test files
- `sample_pdf_file` - Sample PDF file for testing
- `sample_docx_file` - Sample DOCX file for testing
- `mock_openai_client` - Mock OpenAI client
- `mock_pinecone_index` - Mock Pinecone index
- `mock_mongodb_client` - Mock MongoDB client
- `sample_document_data` - Sample document data

### Backend-Specific Fixtures

- `app` - FastAPI app instance
- `client` - Async HTTP client
- `sync_client` - Synchronous HTTP client
- `mock_websocket_manager` - Mock WebSocket manager

### Worker-Specific Fixtures

- `mock_llama_index_readers` - Mock LlamaIndex readers
- `mock_sentence_splitter` - Mock sentence splitter
- `mock_requests_post` - Mock requests.post

## Configuration

### Pytest Configuration

Both backend and worker have `pytest.ini` files with:

- Test discovery patterns
- Coverage settings
- Markers registration
- Logging configuration
- Warning filters

### Environment Variables

Test environment variables are set in `conftest.py`:

```python
os.environ["TESTING"] = "true"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017/docuverse_test"
```

## Coverage Reports

Coverage reports are generated in multiple formats:

- **Terminal**: Shows coverage summary in terminal
- **HTML**: Detailed HTML report in `htmlcov/` directory
- **XML**: XML report for CI/CD integration

### Coverage Thresholds

- **Backend**: 80% minimum coverage
- **Worker**: 75% minimum coverage

## Best Practices

### 1. Test Organization

- Mirror source code structure in test directories
- Use descriptive test class and method names
- Group related tests in classes
- Use appropriate markers for test categorization

### 2. Test Isolation

- Each test should be independent
- Use fixtures for setup and teardown
- Mock external dependencies
- Clean up resources after tests

### 3. Test Data

- Use fixtures for test data
- Create realistic but minimal test data
- Use factories for complex data generation
- Avoid hardcoded values in tests

### 4. Async Testing

- Use `@pytest.mark.asyncio` for async tests
- Use `AsyncClient` for API testing
- Mock async dependencies properly

### 5. Mocking

- Mock external services and APIs
- Use `patch` for dependency injection
- Verify mock calls and arguments
- Don't over-mock - test real interactions when possible

## Continuous Integration

The testing framework is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    make test-coverage
    
- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure proper `PYTHONPATH` setup
2. **Async Test Failures**: Use `pytest-asyncio` plugin
3. **Database Connection**: Use test database configurations
4. **External Service Mocking**: Properly mock third-party services

### Debug Commands

```bash
# Run with verbose output
make test-debug

# Run specific failing test
make test-specific FILE=tests/unit/app/core/test_config.py::TestSettings::test_settings_creation

# Run with pdb debugger
poetry run pytest --pdb
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure good test coverage
3. Add appropriate markers
4. Update this documentation if needed
5. Run full test suite before submitting PR

For questions or issues with testing, please refer to the project documentation or create an issue in the repository. 