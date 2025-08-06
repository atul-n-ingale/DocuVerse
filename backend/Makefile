.PHONY: help install install-dev format lint type-check test test-cov clean pre-commit install-hooks run dev

help: ## Show this help message
	@echo "DocuVerse Backend - Development Commands"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	poetry install --only main

install-dev: ## Install development dependencies
	poetry install --with dev

format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

lint: ## Run ruff linter
	poetry run ruff check .

lint-fix: ## Run ruff linter with auto-fix
	poetry run ruff check --fix .

type-check: ## Run mypy type checking
	poetry run mypy app/ --config-file mypy.ini

type-check-strict: ## Run mypy type checking with strict mode
	poetry run mypy app/ --config-file mypy.ini --strict

type-check-html: ## Run mypy type checking and generate HTML report
	poetry run mypy app/ --config-file mypy.ini --html-report mypy_html_report

# Testing commands
test: ## Run all tests
	poetry run pytest

test-unit: ## Run unit tests only
	poetry run pytest tests/unit/ -m unit

test-integration: ## Run integration tests only
	poetry run pytest tests/integration/ -m integration

test-e2e: ## Run end-to-end tests only
	poetry run pytest tests/e2e/ -m e2e

test-fast: ## Run fast tests only (exclude slow tests)
	poetry run pytest -m "not slow"

test-slow: ## Run slow tests only
	poetry run pytest -m slow

test-coverage: ## Run tests with coverage report
	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing

test-coverage-xml: ## Run tests with XML coverage report
	poetry run pytest --cov=app --cov-report=xml

test-watch: ## Run tests in watch mode
	poetry run pytest-watch

test-debug: ## Run tests with debugging
	poetry run pytest -s -vvv --tb=long

test-parallel: ## Run tests in parallel
	poetry run pytest -n auto

test-specific: ## Run specific test file (usage: make test-specific FILE=path/to/test_file.py)
	poetry run pytest $(FILE) -v

test-marker: ## Run tests with specific marker (usage: make test-marker MARKER=unit)
	poetry run pytest -m $(MARKER)

test-keyword: ## Run tests matching keyword (usage: make test-keyword KEYWORD=test_name)
	poetry run pytest -k $(KEYWORD)

test-failed: ## Run only failed tests from last run
	poetry run pytest --lf

test-clean: ## Clean test artifacts
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage

pre-commit: ## Run pre-commit on all files
	poetry run pre-commit run --all-files

install-hooks: ## Install pre-commit hooks
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg

run: ## Run the FastAPI application
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev: ## Run in development mode with auto-reload
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

check-all: format lint type-check test ## Run all checks (format, lint, type-check, test)

docker-build: ## Build Docker image
	docker build -t docuverse-backend .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env docuverse-backend

docs: ## Generate API documentation
	poetry run mkdocs serve

docs-build: ## Build documentation
	poetry run mkdocs build

security: ## Run security checks
	poetry run bandit -r app/
	poetry run safety check

# Development utilities
shell: ## Start Poetry shell
	poetry shell

add-dep: ## Add a dependency (usage: make add-dep DEP=package_name)
	poetry add $(DEP)

add-dev-dep: ## Add a development dependency (usage: make add-dev-dep DEP=package_name)
	poetry add --group dev $(DEP)

update: ## Update all dependencies
	poetry update

lock: ## Update poetry.lock
	poetry lock

export-requirements: ## Export requirements.txt
	poetry export -f requirements.txt --output requirements.txt --without-hashes 