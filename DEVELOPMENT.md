# DocuVerse Development Guide

This guide covers the development setup, tools, and best practices for the DocuVerse project.

## 🛠️ Development Tools Setup

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Docker & Docker Compose
- Node.js 18+ (for frontend development)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd DocuVerse
   ```

2. **Install development dependencies:**
   ```bash
   # Backend
   cd backend
   poetry install --with dev
   poetry run pre-commit install
   poetry run pre-commit install --hook-type commit-msg
   
   # Worker
   cd ../worker
   poetry install --with dev
   poetry run pre-commit install
   poetry run pre-commit install --hook-type commit-msg
   
   # Frontend
   cd ../frontend
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # Copy environment templates
   cp backend/env_template.txt backend/.env
   cp worker/env_template.txt worker/.env
   cp frontend/.env.development frontend/.env
   
   # Edit the .env files with your configuration
   ```

## 🔧 Development Commands

### Backend (FastAPI)

```bash
cd backend

# Show all available commands
make help

# Install dependencies
make install-dev

# Format code
make format

# Lint code
make lint
make lint-fix

# Type checking
make type-check

# Run tests
make test
make test-cov

# Run the application
make dev

# Run all checks
make check-all

# Pre-commit hooks
make pre-commit
make install-hooks
```

### Worker (Celery)

```bash
cd worker

# Show all available commands
make help

# Install dependencies
make install-dev

# Format and lint
make format
make lint
make lint-fix

# Type checking
make type-check

# Run tests
make test
make test-cov

# Start Celery worker
make worker
make worker-debug

# Start Flower monitoring
make flower

# Celery management
make celery-status
make celery-stats
make celery-registered
```

### Frontend (React)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
npm run lint:fix
```

## 🐳 Docker Development

### Using Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f frontend

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

### Individual Docker Commands

```bash
# Backend
cd backend
make docker-build
make docker-run

# Worker
cd worker
make docker-build
make docker-worker
make docker-flower
```

## 📝 Code Quality Tools

### Backend & Worker

#### 1. **Black** - Code Formatter
- **Purpose**: Automatic code formatting
- **Configuration**: `pyproject.toml`
- **Usage**: `make format` or `poetry run black .`

#### 2. **isort** - Import Sorter
- **Purpose**: Organize and sort imports
- **Configuration**: `pyproject.toml`
- **Usage**: `make format` or `poetry run isort .`

#### 3. **Ruff** - Fast Linter
- **Purpose**: Fast Python linter with auto-fix
- **Configuration**: `pyproject.toml`
- **Usage**: `make lint` or `poetry run ruff check .`
- **Auto-fix**: `make lint-fix` or `poetry run ruff check --fix .`

#### 4. **MyPy** - Type Checker
- **Purpose**: Static type checking
- **Configuration**: `pyproject.toml`
- **Usage**: `make type-check` or `poetry run mypy app/`

#### 5. **Pre-commit** - Git Hooks
- **Purpose**: Run checks before commits
- **Configuration**: `.pre-commit-config.yaml`
- **Usage**: `make install-hooks` to install hooks

### Frontend

#### 1. **ESLint** - JavaScript Linter
- **Purpose**: Code linting and style enforcement
- **Configuration**: `.eslintrc.js`
- **Usage**: `npm run lint`

#### 2. **Prettier** - Code Formatter
- **Purpose**: Automatic code formatting
- **Configuration**: `.prettierrc`
- **Usage**: `npm run format`

## 🧪 Testing

### Backend Testing

```bash
cd backend

# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
poetry run pytest tests/test_specific.py

# Run with verbose output
poetry run pytest -v

# Run tests in watch mode
make test-watch
```

### Worker Testing

```bash
cd worker

# Run all tests
make test

# Run with coverage
make test-cov

# Test Celery tasks
poetry run pytest tests/test_tasks.py
```

### Frontend Testing

```bash
cd frontend

# Run tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

## 🔍 Code Quality Workflow

### Pre-commit Checks

The project uses pre-commit hooks to ensure code quality:

1. **Automatic formatting** with Black and isort
2. **Linting** with Ruff
3. **Type checking** with MyPy
4. **Security checks** with Bandit
5. **File validation** (YAML, JSON, etc.)

### Manual Quality Checks

```bash
# Backend
cd backend
make check-all

# Worker
cd worker
make check-all

# Frontend
cd frontend
npm run lint
npm test
```

## 📚 Documentation

### API Documentation

- **FastAPI Auto-docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Code Documentation

```bash
# Backend
cd backend
make docs        # Serve documentation
make docs-build  # Build documentation
```

## 🔒 Security

### Security Checks

```bash
# Backend
cd backend
make security

# Worker
cd worker
make security
```

### Security Tools

- **Bandit**: Security linter for Python
- **Safety**: Check for known security vulnerabilities
- **Pre-commit hooks**: Prevent committing sensitive data

## 🚀 Deployment

### Production Build

```bash
# Backend
cd backend
make export-requirements
docker build -t docuverse-backend .

# Worker
cd worker
make export-requirements
docker build -t docuverse-worker .

# Frontend
cd frontend
npm run build
```

### Environment Configuration

- **Development**: Use `.env` files in each service directory
- **Production**: Use environment variables or Docker secrets
- **Testing**: Use test-specific environment files

## 🐛 Debugging

### Backend Debugging

```bash
cd backend

# Run with debug logging
make dev

# Use Python debugger
poetry run python -m pdb main.py

# Debug with IPython
poetry run ipython
```

### Worker Debugging

```bash
cd worker

# Run worker in debug mode
make worker-debug

# Monitor Celery tasks
make monitor

# Check worker status
make celery-status
```

### Frontend Debugging

```bash
cd frontend

# Start with React DevTools
npm start

# Debug with browser dev tools
# Open browser and use F12 for developer tools
```

## 📋 Best Practices

### Code Style

1. **Follow PEP 8** for Python code
2. **Use Black** for consistent formatting
3. **Sort imports** with isort
4. **Use type hints** for all functions
5. **Write docstrings** for all public functions

### Git Workflow

1. **Use conventional commits** (enforced by commitizen)
2. **Run pre-commit hooks** before committing
3. **Write meaningful commit messages**
4. **Create feature branches** for new features

### Testing

1. **Write unit tests** for all functions
2. **Achieve high test coverage** (>80%)
3. **Use fixtures** for test data
4. **Mock external dependencies**

### Documentation

1. **Keep README files updated**
2. **Document API endpoints**
3. **Write inline comments** for complex logic
4. **Update changelog** for releases

## 🆘 Troubleshooting

### Common Issues

1. **Poetry lock conflicts**: Run `poetry lock --no-update`
2. **Pre-commit failures**: Run `make pre-commit` to see details
3. **Docker build failures**: Check Dockerfile and dependencies
4. **Test failures**: Check environment variables and dependencies

### Getting Help

1. Check the logs: `docker compose logs -f <service>`
2. Run tests: `make test`
3. Check linting: `make lint`
4. Verify environment: Check `.env` files

## 📞 Support

For development issues:

1. Check the documentation
2. Review the logs
3. Run the test suite
4. Check the issue tracker
5. Contact the development team 