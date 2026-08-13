#!/usr/bin/env python3
"""Test database initialization and table creation."""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import Session
from app.core.db import engine, init_db

print("🔍 Testing database initialization...")
print(f"📁 Database location: {backend_path / 'app.db'}")

try:
    with Session(engine) as session:
        init_db(session)
    print("✅ Database initialized successfully!")
    
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📊 Created tables: {tables}")
    
    required = ["batchexperiment", "batchexperimentrun", "uncertaintyexperiment"]
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"❌ MISSING TABLES: {missing}")
        sys.exit(1)
    else:
        print("✅ All required tables exist!")
        sys.exit(0)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Made with Bob
