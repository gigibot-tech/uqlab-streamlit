"""Backfill best_signals_json for existing experiments.

This script reads summary.json files from the results directory and populates
the best_signals_json column in the database for experiments that don't have it yet.

Usage:
    python scripts/migrations/backfill_best_signals.py
"""

import json
import sys
from pathlib import Path

from sqlmodel import Session, select

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.db import engine
from app.tables import UncertaintyExperiment


def backfill_signals():
    """Backfill best_signals_json from summary.json files."""
    print("Starting backfill of best_signals_json...")

    with Session(engine) as session:
        statement = select(UncertaintyExperiment)
        experiments = session.exec(statement).all()

        print(f"Found {len(experiments)} experiments in database")

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for exp in experiments:
            if exp.best_signals_json:
                skipped_count += 1
                continue

            if not exp.results_path:
                print(f"Experiment {exp.name} has no results_path, skipping")
                skipped_count += 1
                continue

            results_path = Path(exp.results_path)
            summary_file = results_path / "summary.json"

            if not summary_file.exists():
                print(f"No summary.json found for {exp.name} at {summary_file}")
                error_count += 1
                continue

            try:
                with open(summary_file) as f:
                    summary_data = json.load(f)

                one_vs_rest_auroc = summary_data.get("one_vs_rest_auroc", [])

                if not one_vs_rest_auroc:
                    print(f"No one_vs_rest_auroc data in {exp.name}")
                    error_count += 1
                    continue

                best_signals = {"one_vs_rest_auroc": one_vs_rest_auroc}

                exp.best_signals_json = json.dumps(best_signals)
                session.add(exp)

                print(f"Updated {exp.name} with {len(one_vs_rest_auroc)} signals")
                updated_count += 1

            except Exception as e:
                print(f"Error processing {exp.name}: {e}")
                error_count += 1
                continue

        session.commit()

        print("\n" + "=" * 60)
        print("Backfill Summary:")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped (already had data): {skipped_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total processed: {len(experiments)}")
        print("=" * 60)

        if updated_count > 0:
            print("\nBackfill completed successfully!")
            print("Refresh your Streamlit dashboard to see all 7 signals!")
        else:
            print("\nNo experiments needed updating")


if __name__ == "__main__":
    backfill_signals()
