# Backend Startup Fix - Summary

## Problem

When trying to start the FastAPI backend with:
```bash
cd uqlab-streamlit
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You got this error:
```
ModuleNotFoundError: No module named 'app'
```

## Root Cause

**Python's module resolution is relative to the current working directory.**

The backend structure is:
```
uqlab-streamlit/
└── backend/
    └── app/
        └── main.py
```

When you run `uvicorn app.main:app` from `uqlab-streamlit/`, Python looks for:
- `uqlab-streamlit/app/main.py` ❌ (doesn't exist)

When you run it from `uqlab-streamlit/backend/`, Python looks for:
- `uqlab-streamlit/backend/app/main.py` ✅ (exists!)

## Solution

### Quick Fix (Use the startup script)

```bash
cd uqlab-streamlit/backend
./start_backend.sh
```

### Manual Fix

Always start the backend from the `backend/` directory:

```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Files Created

1. **`backend/start_backend.sh`** - Convenient startup script
   - Automatically changes to correct directory
   - Starts uvicorn with proper settings
   - Made executable with `chmod +x`

2. **`BACKEND_STARTUP_GUIDE.md`** - Comprehensive documentation
   - Quick start instructions
   - Explanation of why working directory matters
   - Troubleshooting guide
   - Development workflow

## Verification

After starting correctly, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Then access:
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Workflow

**Terminal 1 - Backend:**
```bash
cd uqlab-streamlit/backend
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd uqlab-streamlit
streamlit run streamlit_app_progressive.py
```

## Key Takeaway

**Always run uvicorn from the directory that contains the `app/` folder.**

This is a common Python packaging pattern where the working directory determines module resolution.