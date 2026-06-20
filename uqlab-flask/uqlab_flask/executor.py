"""Background experiment execution — single worker, one sweep in one go."""

from __future__ import annotations

import json
import logging
import queue
import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from uqlab.runner.pipeline import run as pipeline_run

log = logging.getLogger("uqlab_flask.executor")

_lock = threading.Lock()
_jobs: Dict[str, RunJob] = {}
_sweeps: Dict[str, "SweepGroup"] = {}

_job_queue: queue.Queue[tuple[str, List[RunJob], Path]] = queue.Queue()
_worker_started = False


@dataclass
class RunJob:
    run_id: str
    config_path: Path
    output_dir: Path
    status: str = "queued"
    error: Optional[str] = None
    sweep_group_id: Optional[str] = None
    position: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def run_dir(self) -> Path:
        return self.config_path.parent

    @property
    def status_path(self) -> Path:
        return self.run_dir / "status.json"


@dataclass
class SweepGroup:
    group_id: str
    run_ids: List[str]
    status: str = "queued"
    current_index: int = 0
    total: int = 0
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    @property
    def manifest_path(self) -> Path:
        raise RuntimeError("manifest_path requires experiments_dir")

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "run_ids": self.run_ids,
            "status": self.status,
            "current_index": self.current_index,
            "total": self.total,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sweeps_dir(experiments_dir: Path) -> Path:
    d = experiments_dir / "_sweeps"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _manifest_path(experiments_dir: Path, group_id: str) -> Path:
    return _sweeps_dir(experiments_dir) / f"{group_id}.json"


def _write_manifest(experiments_dir: Path, sweep: SweepGroup) -> None:
    sweep.updated_at = _now_iso()
    path = _manifest_path(experiments_dir, sweep.group_id)
    path.write_text(json.dumps(sweep.to_dict(), indent=2), encoding="utf-8")


def _read_manifest(experiments_dir: Path, group_id: str) -> Optional[SweepGroup]:
    path = _manifest_path(experiments_dir, group_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return SweepGroup(
        group_id=data["group_id"],
        run_ids=list(data.get("run_ids") or []),
        status=data.get("status", "unknown"),
        current_index=int(data.get("current_index") or 0),
        total=int(data.get("total") or 0),
        error=data.get("error"),
        created_at=data.get("created_at") or "",
        updated_at=data.get("updated_at") or "",
    )


def _write_run_status(job: RunJob) -> None:
    payload = {
        "run_id": job.run_id,
        "status": job.status,
        "error": job.error,
        "position": job.position,
        "updated_at": _now_iso(),
        "sweep_group_id": job.sweep_group_id,
    }
    job.status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_run_status(run_dir: Path) -> Optional[dict[str, Any]]:
    path = run_dir / "status.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _infer_run_status(run_dir: Path, recorded: Optional[str], *, allow_interrupted: bool) -> str:
    summary_path = run_dir / "results" / "summary.json"
    if summary_path.is_file():
        return "completed"
    if recorded:
        if allow_interrupted and recorded == "queued":
            return "interrupted"
        return recorded
    if (run_dir / "results").is_dir():
        return "running"
    return "unknown"


def _ensure_worker() -> None:
    global _worker_started
    with _lock:
        if _worker_started:
            return
        thread = threading.Thread(target=_worker_loop, name="uqlab-sweep-worker", daemon=True)
        thread.start()
        _worker_started = True
        log.info("Sweep worker thread started")


def _worker_loop() -> None:
    while True:
        item = _job_queue.get()
        try:
            _process_batch(item)
        except Exception:
            log.exception("Unhandled error in sweep worker batch")
        finally:
            _job_queue.task_done()


def _process_batch(item: tuple[str, List[RunJob], Path]) -> None:
    kind, jobs, experiments_dir = item
    if not jobs:
        return

    group_id = jobs[0].sweep_group_id
    sweep = _sweeps.get(group_id) if group_id else None
    if sweep is None and group_id:
        sweep = _read_manifest(experiments_dir, group_id)

    if sweep:
        sweep.status = "running"
        sweep.total = len(jobs)
        _write_manifest(experiments_dir, sweep)
        with _lock:
            _sweeps[group_id] = sweep

    failures = 0
    for index, job in enumerate(jobs, start=1):
        job.position = index
        if sweep:
            sweep.current_index = index
            _write_manifest(experiments_dir, sweep)

        job.status = "running"
        _write_run_status(job)
        log.info("Run %s started (%s/%s)", job.run_id, index, len(jobs))

        try:
            pipeline_run(job.config_path, job.output_dir)
            job.status = "completed"
            log.info("Run %s completed", job.run_id)
        except Exception as exc:
            job.status = "failed"
            job.error = str(exc)
            failures += 1
            log.exception("Run %s failed", job.run_id)
        _write_run_status(job)

    if sweep:
        if failures == len(jobs):
            sweep.status = "failed"
            sweep.error = "All runs in sweep failed"
        elif failures:
            sweep.status = "partial"
        else:
            sweep.status = "completed"
        _write_manifest(experiments_dir, sweep)
        with _lock:
            _sweeps[group_id] = sweep


def _register_job(job: RunJob) -> None:
    with _lock:
        _jobs[job.run_id] = job
    _write_run_status(job)


def _enqueue(jobs: List[RunJob], experiments_dir: Path, *, kind: str = "sweep") -> None:
    _ensure_worker()
    _job_queue.put((kind, jobs, experiments_dir))


def create_run_job(
    cfg: dict,
    experiments_dir: Path,
    *,
    sweep_group_id: Optional[str] = None,
    name: Optional[str] = None,
    position: int = 0,
    enqueue: bool = False,
) -> RunJob:
    run_id = str(uuid.uuid4())
    run_dir = experiments_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "config.yaml"
    output_dir = run_dir / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)

    meta = {
        "name": name or run_id[:8],
        "created_at": _now_iso(),
        "sweep_group_id": sweep_group_id,
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    job = RunJob(
        run_id=run_id,
        config_path=config_path,
        output_dir=output_dir,
        sweep_group_id=sweep_group_id,
        position=position,
        meta=meta,
    )
    _register_job(job)

    if enqueue:
        _enqueue([job], experiments_dir, kind="single")
    return job


def submit_run(
    cfg: dict,
    experiments_dir: Path,
    *,
    sweep_group_id: Optional[str] = None,
    name: Optional[str] = None,
) -> RunJob:
    return create_run_job(
        cfg,
        experiments_dir,
        sweep_group_id=sweep_group_id,
        name=name,
        enqueue=True,
    )


def submit_sweep(
    workflow: dict,
    experiments_dir: Path,
    *,
    sweep_group_id: Optional[str] = None,
) -> tuple[SweepGroup, list[RunJob]]:
    """Create all run folders, enqueue ONE worker batch — runs sequentially in one go."""
    from uqlab_orchestrator.run_spec import generate_sweep_runs, run_name

    group_id = sweep_group_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ts = group_id
    specs = list(generate_sweep_runs(workflow))
    jobs: list[RunJob] = []

    for index, (sweep_kind, cfg) in enumerate(specs, start=1):
        name = run_name(sweep_kind, cfg, ts)
        jobs.append(
            create_run_job(
                cfg,
                experiments_dir,
                sweep_group_id=group_id,
                name=name,
                position=index,
                enqueue=False,
            )
        )

    sweep = SweepGroup(
        group_id=group_id,
        run_ids=[j.run_id for j in jobs],
        status="queued",
        current_index=0,
        total=len(jobs),
        created_at=_now_iso(),
        updated_at=_now_iso(),
    )
    with _lock:
        _sweeps[group_id] = sweep
    _write_manifest(experiments_dir, sweep)
    _enqueue(jobs, experiments_dir, kind="sweep")
    log.info("Enqueued sweep %s with %s runs", group_id, len(jobs))
    return sweep, jobs


def get_job(
    run_id: str,
    *,
    experiments_dir: Optional[Path] = None,
    allow_interrupted: bool = True,
) -> Optional[RunJob]:
    with _lock:
        job = _jobs.get(run_id)
    if job is not None:
        return job

    if experiments_dir is None:
        try:
            from flask import has_app_context, current_app

            if not has_app_context():
                return None
            experiments_dir = current_app.config["EXPERIMENTS_DIR"]
        except Exception:
            return None

    run_dir = experiments_dir / run_id
    if not run_dir.is_dir():
        return None

    disk = _read_run_status(run_dir) or {}
    meta_path = run_dir / "meta.json"
    meta: dict[str, Any] = {}
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    group_id = disk.get("sweep_group_id") or meta.get("sweep_group_id")
    active_group = group_id and _is_sweep_active(experiments_dir, group_id)

    status = _infer_run_status(
        run_dir,
        disk.get("status"),
        allow_interrupted=allow_interrupted and not active_group,
    )

    return RunJob(
        run_id=run_id,
        config_path=run_dir / "config.yaml",
        output_dir=run_dir / "results",
        status=status,
        error=disk.get("error"),
        sweep_group_id=group_id,
        position=int(disk.get("position") or 0),
        meta=meta,
    )


def _is_sweep_active(experiments_dir: Path, group_id: str) -> bool:
    with _lock:
        sweep = _sweeps.get(group_id)
    if sweep and sweep.status in ("queued", "running"):
        return True
    manifest = _read_manifest(experiments_dir, group_id)
    return manifest is not None and manifest.status in ("queued", "running")


def get_sweep_group(
    group_id: str,
    *,
    experiments_dir: Path,
) -> Optional[SweepGroup]:
    with _lock:
        sweep = _sweeps.get(group_id)
    if sweep is None:
        sweep = _read_manifest(experiments_dir, group_id)
    if sweep is None:
        run_ids = _run_ids_for_group(experiments_dir, group_id)
        if run_ids:
            sweep = _sweep_from_runs(group_id, run_ids, source="inferred")
    if sweep is None:
        return None

    # Reconcile aggregate status from child runs when manifest is stale.
    counts = {"completed": 0, "failed": 0, "running": 0, "queued": 0, "interrupted": 0}
    current_index = 0
    for index, run_id in enumerate(sweep.run_ids, start=1):
        job = get_job(run_id, experiments_dir=experiments_dir, allow_interrupted=True)
        if job is None:
            continue
        counts[job.status] = counts.get(job.status, 0) + 1
        if job.status == "running":
            current_index = index
        elif job.status == "completed":
            current_index = max(current_index, index)

    total = sweep.total or len(sweep.run_ids)
    if counts["running"] or counts["queued"]:
        sweep.status = "running"
    elif counts["completed"] == total:
        sweep.status = "completed"
    elif counts["failed"] == total:
        sweep.status = "failed"
    elif counts["failed"] or counts["interrupted"]:
        sweep.status = "partial"
    sweep.current_index = current_index
    sweep.total = total
    return sweep


def sweep_is_active(sweep: SweepGroup) -> bool:
    return sweep.status in ("queued", "running")


_RUN_NAME_GROUP_RE = re.compile(r"fast_(?:alea|epis)_(\d{8}_\d{6})(?:_|$)")


@dataclass
class SweepHistoryEntry:
    group_id: str
    status: str
    total: int
    completed: int
    failed: int
    active: int
    updated_at: str
    source: str  # manifest | inferred
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_id": self.group_id,
            "status": self.status,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "active": self.active,
            "updated_at": self.updated_at,
            "source": self.source,
            "label": self.label or self.group_id,
        }


def _scan_run_dirs(experiments_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not experiments_dir.is_dir():
        return records
    for child in experiments_dir.iterdir():
        if not child.is_dir() or child.name.startswith("_"):
            continue
        run_id = child.name
        meta: dict[str, Any] = {}
        meta_path = child / "meta.json"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        disk = _read_run_status(child) or {}
        name = str(meta.get("name") or run_id[:8])
        group_id = (
            meta.get("sweep_group_id")
            or disk.get("sweep_group_id")
        )
        if not group_id:
            match = _RUN_NAME_GROUP_RE.search(name)
            if match:
                group_id = match.group(1)
        records.append(
            {
                "run_id": run_id,
                "name": name,
                "group_id": group_id,
                "position": int(disk.get("position") or meta.get("position") or 0),
                "updated_at": disk.get("updated_at") or meta.get("created_at") or "",
            }
        )
    return records


def _run_ids_for_group(experiments_dir: Path, group_id: str) -> list[str]:
    matches = [
        r for r in _scan_run_dirs(experiments_dir)
        if r.get("group_id") == group_id
    ]
    matches.sort(key=lambda r: (r.get("position") or 0, r.get("name") or ""))
    return [r["run_id"] for r in matches]


def _sweep_from_runs(
    group_id: str,
    run_ids: list[str],
    *,
    source: str,
    created_at: str = "",
    updated_at: str = "",
) -> SweepGroup:
    return SweepGroup(
        group_id=group_id,
        run_ids=run_ids,
        status="unknown",
        current_index=0,
        total=len(run_ids),
        created_at=created_at,
        updated_at=updated_at,
    )


def resolve_group_id(experiments_dir: Path, query: str) -> Optional[str]:
    """Smart match: group id, timestamp fragment, run uuid, or experiment name."""
    q = (query or "").strip()
    if not q:
        return None

    q_lower = q.lower()
    known_ids: set[str] = set()
    sweeps_dir = _sweeps_dir(experiments_dir)
    if sweeps_dir.is_dir():
        for path in sweeps_dir.glob("*.json"):
            known_ids.add(path.stem)

    for record in _scan_run_dirs(experiments_dir):
        gid = record.get("group_id")
        if gid:
            known_ids.add(str(gid))

    if q in known_ids:
        return q

    partial = [gid for gid in known_ids if q_lower in gid.lower()]
    if len(partial) == 1:
        return partial[0]
    if len(partial) > 1:
        partial.sort(reverse=True)
        return partial[0]

    for record in _scan_run_dirs(experiments_dir):
        if record["run_id"] == q or q_lower in record["run_id"].lower():
            return record.get("group_id")
        if q_lower in record["name"].lower():
            return record.get("group_id")

    match = _RUN_NAME_GROUP_RE.search(q)
    if match and match.group(1) in known_ids:
        return match.group(1)

    return None


def _count_run_statuses(sweep: SweepGroup, experiments_dir: Path) -> dict[str, int]:
    counts = {"completed": 0, "failed": 0, "active": 0}
    for run_id in sweep.run_ids:
        job = get_job(run_id, experiments_dir=experiments_dir, allow_interrupted=True)
        if job is None:
            continue
        if job.status == "completed":
            counts["completed"] += 1
        elif job.status == "failed":
            counts["failed"] += 1
        elif job.status in ("queued", "running"):
            counts["active"] += 1
    return counts


def _entry_from_sweep(
    sweep: SweepGroup,
    experiments_dir: Path,
    *,
    source: str,
) -> SweepHistoryEntry:
    counts = _count_run_statuses(sweep, experiments_dir)
    return SweepHistoryEntry(
        group_id=sweep.group_id,
        status=sweep.status,
        total=sweep.total,
        completed=counts["completed"],
        failed=counts["failed"],
        active=counts["active"],
        updated_at=sweep.updated_at or sweep.created_at,
        source=source,
        label=sweep.group_id,
    )


def list_sweep_history(
    experiments_dir: Path,
    *,
    limit: int = 40,
) -> list[SweepHistoryEntry]:
    """All sweep groups from manifests + inferred run folders."""
    entries: dict[str, SweepHistoryEntry] = {}

    sweeps_dir = _sweeps_dir(experiments_dir)
    if sweeps_dir.is_dir():
        for path in sorted(sweeps_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            group_id = path.stem
            sweep = get_sweep_group(group_id, experiments_dir=experiments_dir)
            if sweep is None:
                continue
            entries[group_id] = _entry_from_sweep(sweep, experiments_dir, source="manifest")

    for record in _scan_run_dirs(experiments_dir):
        gid = record.get("group_id")
        if not gid or str(gid) in entries:
            continue
        sweep = get_sweep_group(str(gid), experiments_dir=experiments_dir)
        if sweep is None:
            continue
        entries[str(gid)] = _entry_from_sweep(sweep, experiments_dir, source="inferred")

    ordered = sorted(
        entries.values(),
        key=lambda e: e.updated_at or e.group_id,
        reverse=True,
    )
    return ordered[:limit]

