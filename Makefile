# Makefile for UQLab-Streamlit
# Inspired by SPARK Workflow project

.PHONY: help install sync lint format test clean run-backend run-frontend run-all

# Default target
help:
	@echo "UQLab-Streamlit Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install      - Install UV and sync all dependencies"
	@echo "  make sync         - Sync workspace dependencies with UV"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run Ruff linter (check only)"
	@echo "  make format       - Run Ruff formatter and auto-fix issues"
	@echo "  make check        - Run both lint and format checks"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run pytest with coverage"
	@echo "  make test-fast    - Run pytest without coverage"
	@echo ""
	@echo "Running Services:"
	@echo "  make run-backend  - Start FastAPI backend (port 8000)"
	@echo "  make run-frontend - Start Streamlit frontend (port 8501)"
	@echo "  make run-all      - Start both backend and frontend"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove cache files and build artifacts"
	@echo "  make clean-all    - Deep clean including venv and lockfile"

# Setup & Installation
install:
	@echo "📦 Installing UV..."
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "✅ UV installed"
	@echo "📦 Syncing workspace dependencies..."
	uv sync
	@echo "✅ Dependencies synced"

sync:
	@echo "📦 Syncing workspace dependencies..."
	uv sync
	@echo "✅ Dependencies synced"

# Code Quality
lint:
	@echo "🔍 Running Ruff linter..."
	uv run ruff check .
	@echo "✅ Linting complete"

format:
	@echo "🎨 Running Ruff formatter..."
	uv run ruff format .
	uv run ruff check --fix .
	@echo "✅ Formatting complete"

check: lint
	@echo "🔍 Checking code format..."
	uv run ruff format --check .
	@echo "✅ All checks passed"

# Testing
test:
	@echo "🧪 Running tests with coverage..."
	uv run pytest --cov=uqlab --cov=app --cov-report=html --cov-report=term-missing
	@echo "✅ Tests complete. Coverage report: htmlcov/index.html"

test-fast:
	@echo "🧪 Running tests (fast mode)..."
	uv run pytest -v
	@echo "✅ Tests complete"

# Running Services
run-backend:
	@echo "🚀 Starting FastAPI backend on http://localhost:8000..."
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	@echo "🚀 Starting Streamlit frontend on http://localhost:8501..."
	uv run streamlit run streamlit_app_progressive.py

run-all:
	@echo "🚀 Starting both backend and frontend..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:8501"
	@echo ""
	@echo "Press Ctrl+C to stop both services"
	@make -j2 run-backend run-frontend

# Cleanup
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean
	@echo "🧹 Deep cleaning (including venv and lockfile)..."
	rm -rf .venv/ uv.lock 2>/dev/null || true
	@echo "✅ Deep cleanup complete"
	@echo "⚠️  Run 'make install' to reinstall dependencies"

# Development workflow
dev: format test
	@echo "✅ Development checks complete"

# CI/CD simulation
ci: check test
	@echo "✅ CI checks complete"

# Made with Bob
