# Backend Startup Guide

## Quick Start

### Option 1: Using the startup script (Recommended)
```bash
cd uqlab-streamlit/backend
./start_backend.sh
```

### Option 2: Manual startup
```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Important Notes

### ⚠️ Working Directory Matters!

The backend **MUST** be started from the `backend/` directory, not from the project root.

**❌ WRONG** (from project root):
```bash
cd uqlab-streamlit
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Error: ModuleNotFoundError: No module named 'app'
```

**✅ CORRECT** (from backend directory):
```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Success: Backend starts correctly
```

### Why This Happens

Python's module resolution looks for `app` relative to the current working directory:
- When in `uqlab-streamlit/`: Python looks for `uqlab-streamlit/app/` (doesn't exist)
- When in `uqlab-streamlit/backend/`: Python looks for `uqlab-streamlit/backend/app/` (exists!)

## Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── models.py        # SQLAlchemy models
│   ├── crud.py          # Database operations
│   ├── api/             # API routes
│   ├── core/            # Core configuration
│   ├── domain/          # Domain models
│   ├── repositories/    # Data access layer
│   └── services/        # Business logic
├── start_backend.sh     # Startup script
└── pyproject.toml       # Dependencies
```

## Verification

Once started, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXXX] using WatchFiles
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'app'"
**Solution**: Make sure you're in the `backend/` directory before running uvicorn.

### Error: "Address already in use"
**Solution**: Another process is using port 8000. Either:
1. Stop the other process
2. Use a different port: `uvicorn app.main:app --reload --port 8001`

### Error: Missing dependencies
**Solution**: Install backend dependencies:
```bash
cd backend
pip install -e .
# or
uv pip install -e .
```

## Development Workflow

1. **Start backend** (in one terminal):
   ```bash
   cd uqlab-streamlit/backend
   ./start_backend.sh
   ```

2. **Start frontend** (in another terminal):
   ```bash
   cd uqlab-streamlit
   streamlit run streamlit_app_progressive.py
   ```

3. **Run tests**:
   ```bash
   cd uqlab-streamlit/backend
   pytest
   ```

## Environment Variables

The backend uses these environment variables (optional):
- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: JWT secret key
- `API_TOKEN`: Optional API authentication token

Create a `.env` file in the `backend/` directory:
```bash
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=your-secret-key-here
```

## Related Documentation

- [Backend README](backend/README.md) - Detailed backend documentation
- [API Endpoints](backend/API_ENDPOINTS_EXPLAINED.md) - API reference
- [Storage Architecture](backend/STORAGE_ARCHITECTURE.md) - Database design