# Fix Python 3.14 Issue with UV

## Quick Fix with UV

UV can manage Python versions and create virtual environments. Here's how to fix the Python 3.14 compatibility issue:

### Step 1: Install UV (if not installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Create New Environment with Python 3.12

```bash
cd /Users/andrearachetta/Documents/old_pilots

# Remove old venv
rm -rf .venv

# Create new venv with Python 3.12 using uv
uv venv --python 3.12

# Activate it
source .venv/bin/activate
```

### Step 3: Install Dependencies with UV

```bash
cd walaris-cen

# Install backend dependencies
uv pip install -r backend/requirements.txt

# Install streamlit dependencies
uv pip install -r streamlit_requirements.txt

# Install project in editable mode
uv pip install -e .
```

### Step 4: Start Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Start Progressive App (in new terminal)

```bash
cd /Users/andrearachetta/Documents/old_pilots
source .venv/bin/activate
cd walaris-cen
streamlit run streamlit_app_progressive.py
```

---

## Alternative: Use UV's Python Management

UV can also install Python versions for you:

```bash
# Install Python 3.12 via uv
uv python install 3.12

# Create venv with that Python
cd /Users/andrearachetta/Documents/old_pilots
rm -rf .venv
uv venv --python 3.12

# Install dependencies
source .venv/bin/activate
cd walaris-cen
uv pip install -r backend/requirements.txt
uv pip install -r streamlit_requirements.txt
uv pip install -e .
```

---

## Why UV?

UV is much faster than pip:
- **10-100x faster** package installation
- **Built-in Python version management**
- **Compatible with pip** (drop-in replacement)
- **Better dependency resolution**

---

## Verification

After setup:

```bash
# Check Python version
python --version  # Should show 3.12.x

# Check packages
uv pip list | grep -i sqlalchemy

# Test backend
cd walaris-cen/backend
uvicorn app.main:app --reload
```

Should start without the SQLAlchemy error.

---

## One-Line Fix

```bash
cd /Users/andrearachetta/Documents/old_pilots && rm -rf .venv && uv venv --python 3.12 && source .venv/bin/activate && cd walaris-cen && uv pip install -r backend/requirements.txt && uv pip install -r streamlit_requirements.txt && uv pip install -e .
```

Then start backend:
```bash
cd walaris-cen/backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### If Python 3.12 not found:
```bash
# Install it via uv
uv python install 3.12

# Or via homebrew
brew install python@3.12
```

### If uv not installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart terminal
```

### If dependencies fail:
```bash
# Try with pip instead
pip install -r backend/requirements.txt
pip install -r streamlit_requirements.txt
pip install -e .
```

---

## Expected Result

After following these steps:
- ✅ Backend starts on http://0.0.0.0:8000
- ✅ Progressive app starts on http://localhost:8501
- ✅ No SQLAlchemy errors
- ✅ Can create experiments
- ✅ Can run sweeps