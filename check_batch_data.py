b"""
Quick script to check if batch experiment runs have per-signal AUROC data.
Run this to diagnose why only 2 signals are showing.
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.tables import BatchExperimentRun

def check_batch_data():
    """Check if batch runs have result_summary_json with per-signal data."""
    
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    
    with Session(engine) as session:
        # Get all completed batch runs
        stmt = select(BatchExperimentRun).where(
            BatchExperimentRun.status == "completed"
        ).limit(5)
        
        runs = session.execute(stmt).scalars().all()
        
        if not runs:
            print("❌ No completed batch runs found")
            return
        
        print(f"✅ Found {len(runs)} completed batch runs\n")
        
        for i, run in enumerate(runs, 1):
            print(f"Run {i}: {run.run_name}")
            print(f"  Batch ID: {run.batch_experiment_id}")
            print(f"  Swept parameter: {run.swept_parameter} = {run.swept_value_numeric}")
            print(f"  Aggregated AUROC: epistemic={run.epistemic_auroc}, aleatoric={run.aleatoric_auroc}")
            
            if run.result_summary_json:
                try:
                    summary = json.loads(run.result_summary_json)
                    one_vs_rest = summary.get("one_vs_rest_auroc", [])
                    
                    if one_vs_rest:
                        print(f"  ✅ Has per-signal data: {len(one_vs_rest)} signals")
                        for sig in one_vs_rest[:3]:  # Show first 3
                            print(f"    - {sig.get('signal')}: alea={sig.get('aleatoric_like_auroc'):.3f}, epis={sig.get('epistemic_like_auroc'):.3f}")
                        if len(one_vs_rest) > 3:
                            print(f"    ... and {len(one_vs_rest) - 3} more signals")
                    else:
                        print(f"  ⚠️  result_summary_json exists but no 'one_vs_rest_auroc' field")
                        print(f"     Keys in summary: {list(summary.keys())}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Invalid JSON in result_summary_json: {e}")
            else:
                print(f"  ❌ No result_summary_json data")
                print(f"     This run was completed before per-signal tracking was added")
            
            print()
        
        print("\n" + "="*70)
        print("DIAGNOSIS:")
        print("="*70)
        
        has_per_signal = any(
            run.result_summary_json and 
            json.loads(run.result_summary_json).get("one_vs_rest_auroc")
            for run in runs
        )
        
        if has_per_signal:
            print("✅ Some runs have per-signal data")
            print("   If you're still seeing only 2 signals:")
            print("   1. Restart the FastAPI backend server")
            print("   2. Refresh the Streamlit page")
        else:
            print("❌ No runs have per-signal AUROC data")
            print("   SOLUTION: You need to run NEW batch experiments")
            print("   The per-signal data is only captured when experiments run")
            print("   Old experiments don't have this data in the database")
            print("\n   To get per-signal visualization:")
            print("   1. Create and run a NEW batch experiment")
            print("   2. The new runs will capture per-signal AUROC")
            print("   3. Then you'll see all signals in the visualization")

if __name__ == "__main__":
    check_batch_data()

# Made with Bob
