# Frontend Makefile
# React/Node.js development tasks

.PHONY: help install dev build test lint format clean check-deps audit security

# Default target
help:
	@echo "Available commands:"
	@echo "  install           - Install dependencies"
	@echo "  dev               - Start development server"
	@echo "  build             - Build production bundle"
	@echo "  preview           - Preview production build"
	@echo ""
	@echo "Testing:"
	@echo "  test              - Run all tests"
	@echo "  test-unit         - Run unit tests"
	@echo "  test-integration  - Run integration tests"
	@echo "  test-e2e          - Run e2e tests"
	@echo "  test-watch        - Run tests in watch mode"
	@echo "  test-coverage     - Run tests with coverage"
	@echo "  test-ci           - Run tests for CI"
	@echo "  test-debug        - Run tests in debug mode"
	@echo "  test-clean        - Clean test cache"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              - Run ESLint"
	@echo "  lint-fix          - Fix ESLint issues"
	@echo "  format            - Format code with Prettier"
	@echo "  format-check      - Check code formatting"
	@echo "  type-check        - Run TypeScript type checking (if applicable)"
	@echo ""
	@echo "Dependencies:"
	@echo "  check-deps        - Check for outdated dependencies"
	@echo "  audit             - Run security audit"
	@echo "  security          - Run security checks"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean             - Clean build artifacts and cache"
	@echo "  clean-all         - Clean everything including node_modules"
	@echo "  reset             - Reset project (clean + install)"

# Installation
install:
	@echo "Installing dependencies..."
	npm ci

install-dev:
	@echo "Installing dependencies (including dev)..."
	npm install

# Development
dev:
	@echo "Starting development server..."
	npm start

build:
	@echo "Building production bundle..."
	npm run build

preview: build
	@echo "Starting preview server..."
	npx serve -s build -l 3000

# Testing
test:
	@echo "Running all tests..."
	npm test

test-unit:
	@echo "Running unit tests..."
	npm run test:unit

test-integration:
	@echo "Running integration tests..."
	npm run test:integration

test-e2e:
	@echo "Running e2e tests..."
	npm run test:e2e

test-watch:
	@echo "Running tests in watch mode..."
	npm run test:watch

test-coverage:
	@echo "Running tests with coverage..."
	npm run test:coverage

test-ci:
	@echo "Running tests for CI..."
	npm run test:ci

test-debug:
	@echo "Running tests in debug mode..."
	npm run test:debug

test-clean:
	@echo "Cleaning test cache..."
	npm run test:clean

test-failed:
	@echo "Running only failed tests..."
	npm run test:failed

test-changed:
	@echo "Running tests for changed files..."
	npm run test:changed

test-specific:
	@echo "Running specific test (usage: make test-specific PATTERN=TestName)..."
	npm run test:specific -- "$(PATTERN)"

test-file:
	@echo "Running specific test file (usage: make test-file FILE=test.js)..."
	npm run test:file -- "$(FILE)"

# Code Quality
lint:
	@echo "Running ESLint..."
	npx eslint src/ --ext .js,.jsx,.ts,.tsx

lint-fix:
	@echo "Fixing ESLint issues..."
	npx eslint src/ --ext .js,.jsx,.ts,.tsx --fix

format:
	@echo "Formatting code with Prettier..."
	npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,md}"

format-check:
	@echo "Checking code formatting..."
	npx prettier --check "src/**/*.{js,jsx,ts,tsx,json,css,md}"

type-check:
	@echo "Running TypeScript type checking..."
	@if [ -f "tsconfig.json" ]; then \
		npx tsc --noEmit; \
	else \
		echo "No TypeScript configuration found"; \
	fi

# Dependencies
check-deps:
	@echo "Checking for outdated dependencies..."
	npm outdated

audit:
	@echo "Running security audit..."
	npm audit

security:
	@echo "Running security checks..."
	npm audit --audit-level moderate

# Maintenance
clean:
	@echo "Cleaning build artifacts and cache..."
	rm -rf build/
	rm -rf coverage/
	rm -rf .nyc_output/
	npm run test:clean

clean-all: clean
	@echo "Cleaning node_modules..."
	rm -rf node_modules/
	rm -f package-lock.json

reset: clean-all install
	@echo "Project reset complete!"

# Docker commands (if using Docker)
docker-build:
	@echo "Building Docker image..."
	docker build -t docuverse-frontend .

docker-run:
	@echo "Running Docker container..."
	docker run -p 3000:3000 docuverse-frontend

docker-dev:
	@echo "Running Docker in development mode..."
	docker run -p 3000:3000 -v $(PWD)/src:/app/src docuverse-frontend

# Bundle analysis
analyze:
	@echo "Analyzing bundle size..."
	npm run build
	npx serve -s build &
	npx webpack-bundle-analyzer build/static/js/*.js

# Performance testing
lighthouse:
	@echo "Running Lighthouse performance test..."
	@if command -v lighthouse >/dev/null 2>&1; then \
		lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html; \
	else \
		echo "Lighthouse not installed. Install with: npm install -g lighthouse"; \
	fi

# Storybook (if using Storybook)
storybook:
	@echo "Starting Storybook..."
	@if [ -f ".storybook/main.js" ]; then \
		npx storybook dev -p 6006; \
	else \
		echo "Storybook not configured"; \
	fi

storybook-build:
	@echo "Building Storybook..."
	@if [ -f ".storybook/main.js" ]; then \
		npx storybook build; \
	else \
		echo "Storybook not configured"; \
	fi

# Git hooks
pre-commit: format lint test-changed
	@echo "Pre-commit checks passed!"

pre-push: test-ci
	@echo "Pre-push checks passed!"

# Environment setup
setup-env:
	@echo "Setting up environment..."
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "Created .env file from .env.example"; \
	else \
		echo ".env file already exists"; \
	fi

# Health check
health:
	@echo "Checking project health..."
	@echo "Node version: $(shell node --version)"
	@echo "NPM version: $(shell npm --version)"
	@echo "Dependencies status:"
	@npm ls --depth=0 2>/dev/null || echo "Some dependencies may be missing"
	@echo "Build status:"
	@npm run build >/dev/null 2>&1 && echo "✓ Build successful" || echo "✗ Build failed"

# Quick start for new developers
quick-start: install setup-env
	@echo "Quick start complete!"
	@echo "Run 'make dev' to start the development server"

# Production deployment preparation
deploy-prep: clean install test-ci lint format-check build
	@echo "Deployment preparation complete!"
	@echo "Build artifacts are ready in ./build/" 