"""
Run database migration to add best_signals_json column.

Usage:
    python backend/run_migration.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, text
from app.core.db import engine

def run_migration():
    """Run the migration SQL script."""
    migration_file = backend_dir / "migrations" / "add_best_signals_column.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    with open(migration_file) as f:
        sql = f.read()
    
    print("🔄 Running migration...")
    print(f"📄 File: {migration_file}")
    
    try:
        with Session(engine) as session:
            # Check if column already exists
            result = session.exec(text("PRAGMA table_info(uncertaintyexperiment)"))
            columns = [row[1] for row in result]
            
            if 'best_signals_json' in columns:
                print("ℹ️  Column 'best_signals_json' already exists, skipping migration")
                return True
            
            # Execute the SQL
            session.exec(text(sql))
            session.commit()
            print("✅ Migration completed successfully!")
            print("📊 Added column: best_signals_json (TEXT)")
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

# Made with Bob
