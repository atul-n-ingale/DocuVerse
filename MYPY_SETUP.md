# MyPy Type Checker Setup Guide

This guide covers the MyPy type checker configuration and usage for the DocuVerse project.

## 🎯 Overview

MyPy is a static type checker for Python that helps catch type-related errors before runtime. It's configured for both the backend (FastAPI) and worker (Celery) projects with comprehensive settings.

## 📁 Configuration Files

### Backend Configuration
- **`backend/pyproject.toml`** - MyPy settings in Poetry configuration
- **`backend/mypy.ini`** - Dedicated MyPy configuration file

### Worker Configuration
- **`worker/pyproject.toml`** - MyPy settings in Poetry configuration
- **`worker/mypy.ini`** - Dedicated MyPy configuration file

## ⚙️ Configuration Features

### Core Settings
```ini
python_version = 3.11
warn_return_any = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
strict_equality = True
```

### Output Settings
```ini
show_error_codes = True
show_column_numbers = True
show_error_context = True
pretty = True
color_output = True
error_summary = True
```

### Strict Mode Settings
```ini
disallow_any_generics = True
disallow_subclassing_any = True
disallow_untyped_calls = True
no_implicit_reexport = True
strict_optional = True
```

## 🚀 Usage

### Basic Type Checking

```bash
# Backend
cd backend
make type-check

# Worker
cd worker
make type-check

# Both (from root)
make type-check
```

### Strict Type Checking

```bash
# Backend
cd backend
make type-check-strict

# Worker
cd worker
make type-check-strict

# Both (from root)
make type-check-strict
```

### HTML Reports

```bash
# Backend
cd backend
make type-check-html

# Worker
cd worker
make type-check-html

# Both (from root)
make type-check-html
```

### Direct MyPy Commands

```bash
# Basic checking
poetry run mypy app/ --config-file mypy.ini

# Strict mode
poetry run mypy app/ --config-file mypy.ini --strict

# HTML report
poetry run mypy app/ --config-file mypy.ini --html-report mypy_html_report

# Check specific file
poetry run mypy app/main.py --config-file mypy.ini

# Check with verbose output
poetry run mypy app/ --config-file mypy.ini --verbose
```

## 📦 Type Stubs

The project includes type stubs for better type checking:

### Backend Type Stubs
- `types-requests` - HTTP requests
- `types-PyYAML` - YAML processing
- `types-aiofiles` - Async file operations
- `types-python-multipart` - File uploads
- `types-redis` - Redis client
- `types-pymongo` - MongoDB client

### Worker Type Stubs
- `types-requests` - HTTP requests
- `types-PyYAML` - YAML processing
- `types-aiofiles` - Async file operations
- `types-redis` - Redis client
- `types-pymongo` - MongoDB client

## 🔧 Per-Module Configuration

External libraries are configured to ignore missing imports and relax type checking:

```ini
[mypy-llama_index.*]
ignore_missing_imports = True
disallow_untyped_defs = False
disallow_incomplete_defs = False
check_untyped_defs = False
disallow_untyped_decorators = False
```

This pattern is applied to all external dependencies to avoid false positives.

## 📋 Excluded Patterns

The following patterns are excluded from type checking:

```ini
exclude = 
    build,
    dist,
    node_modules,
    .venv,
    venv,
    env,
    __pycache__,
    *.pyc,
    *.pyo,
    *.pyd,
    .pytest_cache,
    .mypy_cache,
    .coverage,
    htmlcov,
    tests,
```

## 🎨 Type Annotations Best Practices

### Function Annotations
```python
from typing import Optional, List, Dict, Any

def process_document(
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process a document and return metadata."""
    pass
```

### Variable Annotations
```python
from typing import List, Optional

# Explicit type annotation
documents: List[str] = []

# Optional types
user_id: Optional[str] = None

# Union types
from typing import Union
file_content: Union[str, bytes] = ""
```

### Class Annotations
```python
from typing import List, Optional
from pydantic import BaseModel

class Document(BaseModel):
    id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = []
```

### Async Function Annotations
```python
from typing import List
import asyncio

async def fetch_documents() -> List[Document]:
    """Fetch documents asynchronously."""
    pass
```

## 🔍 Common MyPy Errors and Solutions

### 1. Missing Return Type
```python
# Error
def get_user():
    return user

# Fix
def get_user() -> User:
    return user
```

### 2. Incompatible Types
```python
# Error
def process_list(items: List[str]) -> None:
    items.append(123)  # Error: int not compatible with str

# Fix
def process_list(items: List[Union[str, int]]) -> None:
    items.append(123)
```

### 3. Optional Types
```python
# Error
def get_name(user: Optional[User]) -> str:
    return user.name  # Error: user might be None

# Fix
def get_name(user: Optional[User]) -> str:
    if user is None:
        return "Unknown"
    return user.name
```

### 4. Type Ignore Comments
```python
# Use sparingly, only when you're sure the error is a false positive
def external_library_call() -> Any:  # type: ignore
    return external_lib.function()
```

## 🧪 Testing with MyPy

### Pre-commit Integration
MyPy is integrated into pre-commit hooks:

```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.13.0
  hooks:
    - id: mypy
      additional_dependencies: [types-requests, types-PyYAML]
      args: [--ignore-missing-imports]
```

### CI/CD Integration
Add to your CI pipeline:

```yaml
- name: Type Check
  run: |
    cd backend && poetry run mypy app/ --config-file mypy.ini
    cd worker && poetry run mypy app/ --config-file mypy.ini
```

## 📊 Type Coverage

### Check Type Coverage
```bash
# Install type coverage tool
poetry add --group dev type-coverage

# Run type coverage
poetry run type-coverage
```

### Generate Coverage Report
```bash
# Generate detailed coverage report
poetry run type-coverage --html-report type_coverage_report
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install missing type stubs
   poetry add --group dev types-{package_name}
   ```

2. **False Positives**
   ```python
   # Use type ignore comments sparingly
   result = external_call()  # type: ignore
   ```

3. **Configuration Issues**
   ```bash
   # Check MyPy configuration
   poetry run mypy --show-config
   ```

### Performance Optimization

1. **Incremental Checking**
   ```bash
   # Use incremental mode for faster subsequent runs
   poetry run mypy app/ --config-file mypy.ini --incremental
   ```

2. **Cache Management**
   ```bash
   # Clear MyPy cache
   rm -rf .mypy_cache/
   ```

## 📚 Additional Resources

- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pydantic Type Validation](https://pydantic-docs.helpmanual.io/)
- [FastAPI Type Checking](https://fastapi.tiangolo.com/python-types/)

## 🎯 Best Practices

1. **Start Gradually**: Don't enable all strict options at once
2. **Use Type Stubs**: Install type stubs for external libraries
3. **Document Types**: Use docstrings to document complex types
4. **Regular Checks**: Run type checking regularly in development
5. **CI Integration**: Include type checking in your CI pipeline
6. **Team Training**: Ensure team members understand type annotations

## 🚀 Next Steps

1. **Install Dependencies**: `make install-dev`
2. **Run Initial Check**: `make type-check`
3. **Fix Type Errors**: Address any type issues found
4. **Enable Strict Mode**: Gradually enable stricter checking
5. **Add to CI**: Integrate into your CI/CD pipeline 