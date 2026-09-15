"""Run database migration to add optional method_type column to batchexperiment.

This column is nullable for backward compatibility. Existing experiments will have NULL values.

Usage:
    python scripts/migrations/add_method_type_column.py
"""

import sqlite3
import sys
from pathlib import Path


def run_migration():
    """Execute the method_type column migration."""
    backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
    sys.path.insert(0, str(backend_dir))

    from app.core.runtime_paths import sqlite_db_path

    db_path = sqlite_db_path()

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        print("The database will be created automatically when you start the backend")
        return False

    migration_path = backend_dir / "migrations" / "add_method_type_column.sql"

    if not migration_path.exists():
        print(f"Migration file not found at {migration_path}")
        return False

    with open(migration_path) as f:
        migration_sql = f.read()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(batchexperiment)")
        columns = [row[1] for row in cursor.fetchall()]

        if "method_type" in columns:
            print("Column 'method_type' already exists in batchexperiment table")
            print("No migration needed")
            conn.close()
            return True

        print("Running migration: add method_type column...")

        cursor.executescript(migration_sql)
        conn.commit()

        cursor.execute("PRAGMA table_info(batchexperiment)")
        columns_after = [row[1] for row in cursor.fetchall()]

        if "method_type" in columns_after:
            print("Migration successful!")
            print("Added 'method_type' column to batchexperiment table (nullable)")

            cursor.execute("SELECT COUNT(*) FROM batchexperiment")
            row_count = cursor.fetchone()[0]
            if row_count > 0:
                print(f"Existing {row_count} rows remain with NULL values (backward compatible)")
            else:
                print("No existing rows to update")
        else:
            print("Migration failed: column not found after migration")
            conn.close()
            return False

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add method_type Column")
    print("=" * 60)
    print()

    success = run_migration()

    print()
    if success:
        print("Migration completed successfully!")
        print("You can now restart the backend server")
    else:
        print("Migration failed")
        print("Please check the error messages above")
    print()
