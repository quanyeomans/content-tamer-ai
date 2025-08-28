# Content Tamer AI - Compliance-as-Code Makefile
# Automated security, quality, and dependency management

.PHONY: help install install-dev format lint type-check test clean run compliance-check security-scan quality-check

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

# ===== COMPLIANCE-AS-CODE FRAMEWORK =====

compliance-check: security-scan quality-check format test ## 🚨 MANDATORY: Complete compliance pipeline before commit
	@echo "✅ All compliance checks passed!"
	@echo "🚀 Ready for commit"

security-scan: ## 🔒 Run comprehensive security analysis (Bandit + Safety)
	@echo "🔒 Running security analysis..."
	@echo "📊 Bandit (SAST Security Scan):"
	bandit -r src/ -f text -ll
	@echo ""
	@echo "📊 Safety (Dependency Vulnerability Scan):"
	safety check
	@echo "✅ Security scan complete"

quality-check: ## 📈 Run code quality analysis (Pylint + Flake8 + MyPy)
	@echo "📈 Running code quality analysis..."
	@echo "📊 Pylint (Code Quality):"
	pylint src/ --fail-under=8.0
	@echo ""
	@echo "📊 Flake8 (PEP8 Compliance):"
	flake8 src/ --max-line-length=100
	@echo ""
	@echo "📊 MyPy (Type Checking):"
	mypy src/ --ignore-missing-imports
	@echo "✅ Quality check complete"

security-only: ## 🛡️ Security-focused pipeline (for security work)
	@echo "🛡️ Security-focused pipeline..."
	bandit -r src/ -f text
	safety check --json
	python -m pytest tests/test_security.py -v
	@echo "✅ Security pipeline complete"

quick-check: ## ⚡ Quick development checks (faster than full compliance)
	@echo "⚡ Running quick development checks..."
	bandit -r src/ -ll -f text
	flake8 src/ --max-line-length=100
	@echo "✅ Quick check complete"

generate-reports: ## 📊 Generate detailed compliance reports for CI/CD
	@echo "📊 Generating compliance reports..."
	mkdir -p reports
	bandit -r src/ -f json -o reports/security-report.json || true
	safety check --json --output reports/dependency-report.json || true
	pylint src/ --output-format=json > reports/quality-report.json || true
	pytest tests/ --cov=src --cov-report=json --cov-report=html:reports/coverage || true
	@echo "✅ Reports generated in reports/ directory"

install-sast: ## 📦 Install SAST and security analysis tools
	@echo "📦 Installing SAST tools..."
	pip install bandit safety pylint flake8 mypy black isort
	@echo "✅ SAST tools installed"

compliance-help: ## ❓ Show compliance framework help
	@echo "🏗️ Content Tamer AI - Compliance-as-Code Framework"
	@echo ""
	@echo "🚨 MANDATORY before any commit:"
	@echo "   make compliance-check"
	@echo ""
	@echo "📊 Individual checks:"
	@echo "   make security-scan     - Security analysis (Bandit + Safety)"
	@echo "   make quality-check     - Code quality (Pylint + Flake8 + MyPy)" 
	@echo "   make security-only     - Security-focused development"
	@echo "   make quick-check       - Fast feedback during development"
	@echo ""
	@echo "🎯 Gate Requirements:"
	@echo "   • Security: No HIGH/MEDIUM Bandit issues, No CVEs"
	@echo "   • Quality: Pylint ≥8.0/10, Flake8 clean, MyPy clean"
	@echo "   • Tests: All tests pass, coverage maintained"
	@echo "   • Format: Black + isort applied"