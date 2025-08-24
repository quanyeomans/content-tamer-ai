# Makefile for AI-Powered Document Organization System
# Cross-platform commands for development tasks

.PHONY: help install install-dev format lint type-check test test-verbose clean run

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -e .[dev]
	pip install pre-commit
	pre-commit install

format: ## Format code with Black and isort
	python -m black src/
	python -m isort src/

lint: ## Lint code with flake8
	python -m flake8 src/ --statistics

type-check: ## Run type checking with Pyright
	python -m pyright src/

type-check-mypy: ## Run type checking with MyPy
	python -m mypy src/

test: ## Run tests
	python -m pytest tests/ -v

test-coverage: ## Run tests with coverage
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

test-integration: ## Run integration tests only
	python -m pytest tests/test_integration.py -v

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/ 2>/dev/null || true

run: ## Run the application with default settings
	python run.py

run-help: ## Show application help
	python run.py --help

run-models: ## List available AI models
	python run.py --list-models

check-all: format lint type-check test ## Run all quality checks

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

build: ## Build package
	python -m build

install-local: ## Install package locally for testing
	pip install -e .

# Development workflow targets
dev-setup: install-dev ## Complete development setup
	@echo "Development environment ready!"
	@echo "Run 'make help' to see available commands"

ci: check-all ## Run continuous integration checks
	@echo "All CI checks passed!"