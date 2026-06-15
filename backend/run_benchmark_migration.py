"""
Migration script to add UQ Benchmarks tables to the database.

This script creates the new benchmarkresult and benchmarksweep tables
for storing results from the uq_benchmarks package.

Usage:
    python backend/run_benchmark_migration.py
"""

import sqlite3
from pathlib import Path


def run_migration():
    """Run the benchmark tables migration."""
    # Database path
    db_path = Path(__file__).parent / "app.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("   The database will be created automatically when you start the backend.")
        return
    
    # Read migration SQL
    migration_path = Path(__file__).parent / "migrations" / "add_benchmark_tables.sql"
    
    if not migration_path.exists():
        print(f"❌ Migration file not found at {migration_path}")
        return
    
    with open(migration_path, "r") as f:
        migration_sql = f.read()
    
    # Connect and execute
    print(f"📊 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Running migration...")
        cursor.executescript(migration_sql)
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('benchmarkresult', 'benchmarksweep')
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        if len(tables) == 2:
            print(f"✅ Verified: Created {len(tables)} tables")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print(f"⚠️  Warning: Expected 2 tables, found {len(tables)}")
            
    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("UQ Benchmarks Database Migration")
    print("=" * 60)
    run_migration()
    print("=" * 60)

# Made with Bob
