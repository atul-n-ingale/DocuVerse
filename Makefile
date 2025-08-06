.PHONY: help install install-dev format lint test clean docker-up docker-down docker-build docker-logs dev-setup

help: ## Show this help message
	@echo "DocuVerse - Complete Development Commands"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd backend && poetry install --with dev
	@echo "Installing worker dependencies..."
	cd worker && poetry install --with dev
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ All dependencies installed!"

install-dev: ## Install development dependencies and setup pre-commit hooks
	@echo "Installing development dependencies..."
	cd backend && poetry install --with dev
	cd worker && poetry install --with dev
	cd frontend && npm install
	@echo "Setting up pre-commit hooks..."
	cd backend && poetry run pre-commit install
	cd backend && poetry run pre-commit install --hook-type commit-msg
	cd worker && poetry run pre-commit install
	cd worker && poetry run pre-commit install --hook-type commit-msg
	@echo "✅ Development environment setup complete!"

format: ## Format all code
	@echo "Formatting backend code..."
	cd backend && poetry run black .
	cd backend && poetry run isort .
	@echo "Formatting worker code..."
	cd worker && poetry run black .
	cd worker && poetry run isort .
	@echo "Formatting frontend code..."
	cd frontend && make format
	@echo "✅ All code formatted!"

lint: ## Lint all code
	@echo "Linting backend code..."
	cd backend && poetry run ruff check .
	@echo "Linting worker code..."
	cd worker && poetry run ruff check .
	@echo "Linting frontend code..."
	cd frontend && make lint
	@echo "✅ All code linted!"

lint-fix: ## Lint and fix all code
	@echo "Linting and fixing backend code..."
	cd backend && poetry run ruff check --fix .
	@echo "Linting and fixing worker code..."
	cd worker && poetry run ruff check --fix .
	@echo "Linting and fixing frontend code..."
	cd frontend && make lint-fix
	@echo "✅ All code linted and fixed!"

type-check: ## Run type checking on all Python code
	@echo "Type checking backend code..."
	cd backend && poetry run mypy app/ --config-file mypy.ini
	@echo "Type checking worker code..."
	cd worker && poetry run mypy app/ --config-file mypy.ini
	@echo "✅ All type checks passed!"

type-check-strict: ## Run strict type checking on all Python code
	@echo "Type checking backend code (strict mode)..."
	cd backend && poetry run mypy app/ --config-file mypy.ini --strict
	@echo "Type checking worker code (strict mode)..."
	cd worker && poetry run mypy app/ --config-file mypy.ini --strict
	@echo "✅ All strict type checks passed!"

type-check-html: ## Run type checking and generate HTML reports
	@echo "Type checking backend code with HTML report..."
	cd backend && poetry run mypy app/ --config-file mypy.ini --html-report mypy_html_report
	@echo "Type checking worker code with HTML report..."
	cd worker && poetry run mypy app/ --config-file mypy.ini --html-report mypy_html_report
	@echo "✅ Type checking HTML reports generated!"

test: ## Run all tests for backend, worker, and frontend
	@echo "Running backend tests..."
	cd backend && poetry run pytest
	@echo "Running worker tests..."
	cd worker && poetry run pytest
	@echo "Running frontend tests..."
	cd frontend && make test
	@echo "✅ All tests passed!"

test-unit: ## Run unit tests for backend, worker, and frontend
	@echo "Running backend unit tests..."
	cd backend && poetry run pytest tests/unit/ -m unit
	@echo "Running worker unit tests..."
	cd worker && poetry run pytest tests/unit/ -m unit
	@echo "Running frontend unit tests..."
	cd frontend && make test-unit
	@echo "✅ All unit tests passed!"

test-integration: ## Run integration tests for backend, worker, and frontend
	@echo "Running backend integration tests..."
	cd backend && poetry run pytest tests/integration/ -m integration
	@echo "Running worker integration tests..."
	cd worker && poetry run pytest tests/integration/ -m integration
	@echo "Running frontend integration tests..."
	cd frontend && make test-integration
	@echo "✅ All integration tests passed!"

test-e2e: ## Run end-to-end tests for backend, worker, and frontend
	@echo "Running backend e2e tests..."
	cd backend && poetry run pytest tests/e2e/ -m e2e
	@echo "Running worker e2e tests..."
	cd worker && poetry run pytest tests/e2e/ -m e2e
	@echo "Running frontend e2e tests..."
	cd frontend && make test-e2e
	@echo "✅ All e2e tests passed!"

test-coverage: ## Run tests with coverage for backend, worker, and frontend
	@echo "Running backend tests with coverage..."
	cd backend && poetry run pytest --cov=app --cov-report=html:htmlcov/backend --cov-report=term-missing
	@echo "Running worker tests with coverage..."
	cd worker && poetry run pytest --cov=app --cov-report=html:htmlcov/worker --cov-report=term-missing
	@echo "Running frontend tests with coverage..."
	cd frontend && make test-coverage
	@echo "✅ All tests with coverage completed!"

test-fast: ## Run fast tests only (exclude slow tests)
	@echo "Running backend fast tests..."
	cd backend && poetry run pytest -m "not slow"
	@echo "Running worker fast tests..."
	cd worker && poetry run pytest -m "not slow"
	@echo "Running frontend fast tests..."
	cd frontend && make test-unit
	@echo "✅ All fast tests passed!"

test-backend: ## Run all backend tests
	@echo "Running backend tests..."
	cd backend && poetry run pytest
	@echo "✅ Backend tests passed!"

test-worker: ## Run all worker tests
	@echo "Running worker tests..."
	cd worker && poetry run pytest
	@echo "✅ Worker tests passed!"

test-clean: ## Clean test artifacts for both backend and worker
	@echo "Cleaning backend test artifacts..."
	cd backend && rm -rf htmlcov/ .pytest_cache/ .coverage coverage.xml
	@echo "Cleaning worker test artifacts..."
	cd worker && rm -rf htmlcov/ .pytest_cache/ .coverage coverage.xml
	@echo "✅ Test artifacts cleaned!"

clean: ## Clean all generated files
	@echo "Cleaning backend..."
	cd backend && find . -type f -name "*.pyc" -delete
	cd backend && find . -type d -name "__pycache__" -delete
	cd backend && rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ .coverage
	@echo "Cleaning worker..."
	cd worker && find . -type f -name "*.pyc" -delete
	cd worker && find . -type d -name "__pycache__" -delete
	cd worker && rm -rf .pytest_cache/ .mypy_cache/ htmlcov/ .coverage
	@echo "Cleaning frontend..."
	cd frontend && rm -rf node_modules/ build/ .cache/
	@echo "✅ All generated files cleaned!"

docker-up: ## Start all Docker services
	docker compose up -d
	@echo "✅ All services started!"

docker-down: ## Stop all Docker services
	docker compose down
	@echo "✅ All services stopped!"

docker-build: ## Build all Docker images
	docker compose build
	@echo "✅ All images built!"

docker-logs: ## Show logs for all services
	docker compose logs -f

docker-logs-backend: ## Show backend logs
	docker compose logs -f backend

docker-logs-worker: ## Show worker logs
	docker compose logs -f worker

docker-logs-frontend: ## Show frontend logs
	docker compose logs -f frontend

dev-setup: ## Complete development setup
	@echo "Setting up complete development environment..."
	make install-dev
	make docker-build
	@echo "✅ Development environment setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy and configure environment files:"
	@echo "   cp backend/env_template.txt backend/.env"
	@echo "   cp worker/env_template.txt worker/.env"
	@echo "   cp frontend/.env.development frontend/.env"
	@echo "2. Start services: make docker-up"
	@echo "3. Access the application:"
	@echo "   - Frontend: http://localhost:3000"
	@echo "   - Backend API: http://localhost:8000"
	@echo "   - API Docs: http://localhost:8000/docs"
	@echo "   - Flower Monitor: http://localhost:5555"

check-all: format lint type-check test ## Run all quality checks

pre-commit-all: ## Run pre-commit on all projects
	@echo "Running pre-commit on backend..."
	cd backend && poetry run pre-commit run --all-files
	@echo "Running pre-commit on worker..."
	cd worker && poetry run pre-commit run --all-files
	@echo "✅ All pre-commit checks passed!"

security: ## Run security checks on all projects
	@echo "Running security checks on backend..."
	cd backend && poetry run bandit -r app/
	@echo "Running security checks on worker..."
	cd worker && poetry run bandit -r app/
	@echo "✅ All security checks passed!"

# Frontend-specific commands
frontend-dev: ## Start frontend development server
	cd frontend && make dev

frontend-build: ## Build frontend for production
	cd frontend && make build

frontend-preview: ## Preview frontend production build
	cd frontend && make preview

frontend-test: ## Run all frontend tests
	cd frontend && make test

frontend-test-watch: ## Run frontend tests in watch mode
	cd frontend && make test-watch

frontend-lint: ## Lint frontend code
	cd frontend && make lint

frontend-format: ## Format frontend code
	cd frontend && make format

frontend-clean: ## Clean frontend build artifacts
	cd frontend && make clean

frontend-deps: ## Check frontend dependencies
	cd frontend && make check-deps

frontend-audit: ## Run frontend security audit
	cd frontend && make audit

# Development utilities
shell-backend: ## Start backend Poetry shell
	cd backend && poetry shell

shell-worker: ## Start worker Poetry shell
	cd worker && poetry shell

# Service management
start-backend: ## Start backend service
	cd backend && poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

start-worker: ## Start worker service
	cd worker && poetry run celery -A app.celery_app worker --loglevel=info

start-flower: ## Start Flower monitoring
	cd worker && poetry run celery -A app.celery_app flower --port=5555

start-frontend: ## Start frontend service
	cd frontend && npm start

# All services development
dev-all: ## Start all services in development mode
	@echo "Starting all services in development mode..."
	@echo "This will start backend, worker, and frontend in parallel"
	@echo "Use Ctrl+C to stop all services"
	make -j3 dev-backend dev-worker frontend-dev

# Database management
db-reset: ## Reset all databases (WARNING: This will delete all data)
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v; \
		docker compose up -d mongodb redis; \
		echo "✅ Databases reset!"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# Monitoring
status: ## Show status of all services
	@echo "Docker services:"
	docker compose ps
	@echo ""
	@echo "Backend health:"
	curl -s http://localhost:8000/health || echo "Backend not running"
	@echo ""
	@echo "Frontend health:"
	curl -s http://localhost:3000 > /dev/null && echo "Frontend running" || echo "Frontend not running"
	@echo ""
	@echo "Worker status:"
	cd worker && poetry run celery -A app.celery_app inspect active || echo "Worker not running"

# Documentation
docs: ## Generate all documentation
	@echo "Generating backend documentation..."
	cd backend && poetry run mkdocs build
	@echo "✅ Documentation generated!"

docs-serve: ## Serve documentation
	@echo "Serving backend documentation..."
	cd backend && poetry run mkdocs serve

# Deployment helpers
build-prod: ## Build all services for production
	@echo "Building backend for production..."
	cd backend && make export-requirements
	@echo "Building worker for production..."
	cd worker && make export-requirements
	@echo "Building frontend for production..."
	cd frontend && make build
	@echo "✅ All services built for production!"

# Quick development commands
dev-backend: ## Start backend in development mode
	cd backend && make dev

dev-worker: ## Start worker in development mode
	cd worker && make worker-debug

dev-frontend: ## Start frontend in development mode
	cd frontend && make dev

# Complete project setup
setup-all: install-dev ## Complete project setup for new developers
	@echo "Setting up all services..."
	cd frontend && make setup-env
	@echo "✅ Complete project setup finished!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Start Docker services: make docker-up"
	@echo "2. Start all development services: make dev-all"
	@echo "3. Open http://localhost:3000 for frontend"
	@echo "4. Open http://localhost:8000/docs for API docs"

# Health checks for all services
health-all: ## Check health of all services
	@echo "Checking health of all services..."
	cd backend && make health
	cd worker && make health
	cd frontend && make health
	@echo "✅ All services health checked!"

# Clean all projects
clean-all: ## Clean all build artifacts and caches
	@echo "Cleaning all projects..."
	cd backend && make clean
	cd worker && make clean
	cd frontend && make clean
	@echo "✅ All projects cleaned!"

# Reset all projects
reset-all: ## Reset all projects (clean + install)
	@echo "Resetting all projects..."
	cd backend && make reset
	cd worker && make reset
	cd frontend && make reset
	@echo "✅ All projects reset!" 