"""
Persistent data paths for the FastAPI backend (no ``uqlab`` import required).

Override with env ``UQLAB_DATA_DIR``. Default: ``<repo>/data/``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union
from uuid import UUID

from app.storage.factory import get_storage_backend

# backend/app/core/runtime_paths.py -> uqlab-streamlit/
_REPO_ROOT = Path(__file__).resolve().parents[3]


def data_root() -> Path:
    raw = os.environ.get("UQLAB_DATA_DIR", "").strip()
    root = Path(raw).expanduser() if raw else _REPO_ROOT / "data"
    prepared = get_storage_backend().prepare_directory(root)
    return prepared.resolve()


def sqlite_db_path() -> Path:
    return data_root() / "uqlab.db"


def experiments_root() -> Path:
    root = data_root() / "experiments"
    return get_storage_backend().prepare_directory(root)


def experiment_dir(experiment_id: Union[str, UUID]) -> Path:
    return experiments_root() / str(experiment_id)


def experiment_results_dir(experiment_id: Union[str, UUID]) -> Path:
    return experiment_dir(experiment_id) / "results"


def _results_dir_has_artifacts(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "summary.json").is_file() or (path / "results.pt").is_file():
        return True
    if (path / "per_sample_signals.csv").is_file() or (path / "experiment.log").is_file():
        return True
    zwischen = path / "zwischen"
    return zwischen.is_dir() and any(zwischen.glob("*.pt"))


def resolve_experiment_results_dir(
    experiment_id: Union[str, UUID],
    *,
    results_path: str | Path | None = None,
) -> Path:
    eid = str(experiment_id)
    candidates: list[Path] = []
    if results_path:
        raw = Path(results_path)
        candidates.append(raw if raw.name == "results" else raw / "results")
    candidates.append(experiment_results_dir(eid))
    candidates.append(Path("/tmp/uqlab_experiments") / eid / "results")
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        if path.is_dir() and _results_dir_has_artifacts(path):
            return path
    return experiment_results_dir(eid)


def batch_root(batch_id: Union[str, UUID]) -> Path:
    return get_storage_backend().prepare_directory(experiments_root() / f"batch_{batch_id}")
