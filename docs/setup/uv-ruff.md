# UV & Ruff Setup Guide

This document explains the UV workspace and Ruff configuration adopted from the SPARK workflow project.

## 🚀 Quick Start

```bash
# 1. Install UV (ultra-fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install all workspace dependencies
cd uqlab-streamlit
uv sync

# 3. Run Ruff linting and formatting
uv run ruff check --fix .
uv run ruff format .
```

## 📦 UV - Ultra-Fast Package Manager

### What is UV?

UV is a Rust-based Python package manager that's **10-100x faster** than pip. It's created by Astral (same team behind Ruff).

### Key Features

- ⚡ **Blazing fast**: 10-100x faster than pip
- 🔒 **Deterministic**: Lockfile (`uv.lock`) ensures reproducible installs
- 📦 **Workspace support**: Manage multiple packages in a monorepo
- 🎯 **Drop-in replacement**: Works like pip but faster
- 💾 **Global cache**: Avoids re-downloading packages

### UV Workspace Structure

Our project uses a UV workspace to manage multiple packages:

```
uqlab-streamlit/
├── pyproject.toml          # Root workspace config
├── src/uqlab/              # Core ML framework (submodule)
│   └── pyproject.toml
└── backend/                # FastAPI backend
    └── pyproject.toml
```

**Root `pyproject.toml` workspace config:**
```toml
[tool.uv.workspace]
members = [
    "src/uqlab",
    "backend",
]
```

### Common UV Commands

```bash
# Install all workspace dependencies
uv sync

# Add a new dependency to current package
uv add pandas

# Add a dev dependency
uv add --dev pytest

# Install specific package from workspace
uv pip install -e src/uqlab

# Update all dependencies
uv lock --upgrade

# Run a command in the UV environment
uv run python script.py
uv run pytest
uv run streamlit run streamlit_app_progressive.py

# Create a new virtual environment
uv venv

# Activate the environment (if needed)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### Speed Comparison

```bash
# Installing numpy + pandas + scikit-learn + torch
pip install:     ~120 seconds
uv pip install:  ~5 seconds   (24x faster!)

# Full workspace sync
pip install -r requirements.txt:  ~180 seconds
uv sync:                          ~8 seconds   (22x faster!)
```

## 🎨 Ruff - All-in-One Linter & Formatter

### What is Ruff?

Ruff is an extremely fast Python linter and code formatter written in Rust. It **replaces 5+ tools** with a single fast tool.

### What Ruff Replaces

| Old Tool | Purpose | Ruff Equivalent |
|----------|---------|-----------------|
| **Flake8** | Linting | `ruff check` |
| **Black** | Formatting | `ruff format` |
| **isort** | Import sorting | `ruff check --select I` |
| **pyupgrade** | Syntax modernization | `ruff check --select UP` |
| **autoflake** | Remove unused imports | `ruff check --select F401` |

### Common Ruff Commands

```bash
# Check code for issues (linting)
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code (like Black)
ruff format .

# Check specific file
ruff check myfile.py

# Show all violations with details
ruff check --output-format=full .

# Check only specific rules
ruff check --select E,W,F .

# Watch mode (auto-fix on save)
ruff check --watch .
```

### Ruff Configuration

Our `pyproject.toml` includes comprehensive Ruff configuration:

```toml
[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade (modernize Python syntax)
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
fixable = ["ALL"]  # Auto-fix everything possible
```

### Speed Comparison

```bash
# Linting a large codebase
Flake8 + Black + isort:  ~60 seconds
Ruff:                    ~0.5 seconds  (120x faster!)
```

## 🔄 Migration from Old Tools

### Before (Multiple Tools)

```bash
# Old workflow required multiple tools
pip install black isort flake8 pyupgrade autoflake

# Run each tool separately
black .
isort .
flake8 .
pyupgrade --py310-plus **/*.py
autoflake --remove-all-unused-imports -i **/*.py
```

### After (Single Tool)

```bash
# New workflow with Ruff
uv add --dev ruff

# Run once
ruff check --fix .
ruff format .
```

## 📝 Pre-commit Hook (Optional)

Add Ruff to your pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Install:
```bash
uv add --dev pre-commit
uv run pre-commit install
```

## 🎯 Recommended Workflow

### Daily Development

```bash
# 1. Start your day - sync dependencies
uv sync

# 2. Before committing - lint and format
uv run ruff check --fix .
uv run ruff format .

# 3. Run tests
uv run pytest

# 4. Start development server
uv run streamlit run streamlit_app_progressive.py
```

### Adding New Dependencies

```bash
# Add to root project
uv add requests

# Add to specific workspace member
cd backend
uv add fastapi

# Add dev dependency
uv add --dev pytest
```

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      
      - name: Install dependencies
        run: uv sync
      
      - name: Run Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .
      
      - name: Run tests
        run: uv run pytest
```

## 🆚 Comparison with SPARK Workflow

### Similarities

Both projects now use:
- ✅ UV for package management
- ✅ Ruff for linting/formatting
- ✅ Workspace structure for monorepo
- ✅ Fast CI/CD pipelines

### Differences

| Aspect | SPARK | UQLab-Streamlit |
|--------|-------|-----------------|
| **Python Version** | 3.13 (strict) | 3.10+ (flexible) |
| **Workspace Members** | 12 services | 2 packages |
| **Line Length** | 120 | 120 |
| **Additional Tools** | Pyrefly | Pytest |

## 🐛 Troubleshooting

### UV Issues

**Problem**: `uv: command not found`
```bash
# Solution: Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal
```

**Problem**: Dependency conflicts
```bash
# Solution: Clear cache and re-sync
rm -rf .venv uv.lock
uv sync
```

### Ruff Issues

**Problem**: Too many errors
```bash
# Solution: Fix incrementally
ruff check --select E,W .  # Start with basic errors
ruff check --fix .         # Auto-fix what's possible
```

**Problem**: Conflicts with existing formatters
```bash
# Solution: Remove old tools
uv remove black isort flake8
# Delete old config files
rm .flake8 .isort.cfg
```

## 📚 Additional Resources

- **UV Documentation**: https://docs.astral.sh/uv/
- **Ruff Documentation**: https://docs.astral.sh/ruff/
- **SPARK Workflow**: Reference implementation in `../spark-workflow/`

## 🎉 Benefits Summary

### UV Benefits
- ⚡ 10-100x faster installs
- 🔒 Reproducible builds with lockfile
- 📦 Workspace support for monorepo
- 💾 Global cache saves disk space

### Ruff Benefits
- ⚡ 10-100x faster than old tools
- 🔧 Auto-fixes most issues
- 📏 800+ rules from popular linters
- 🎨 Replaces 5+ tools with one

### Combined Benefits
- 🚀 Faster development workflow
- 🎯 Consistent code style
- 🔄 Easier CI/CD integration
- 📦 Better dependency management

---

**Made with ❤️ inspired by SPARK Workflow**