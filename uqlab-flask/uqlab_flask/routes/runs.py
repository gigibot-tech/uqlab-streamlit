"""Run status API."""

from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, request

from uqlab_orchestrator.run_spec import build_run_yaml, validate_run_yaml
from uqlab_flask.executor import (
    get_job,
    get_sweep_group,
    list_sweep_history,
    resolve_group_id,
    submit_run,
    submit_sweep,
)

bp = Blueprint("runs", __name__)


@bp.post("/runs")
def create_run():
    payload = request.get_json(force=True) or {}
    if "workflow" in payload and payload.get("sweep", True):
        sweep, jobs = submit_sweep(payload["workflow"], current_app.config["EXPERIMENTS_DIR"])
        return jsonify(
            {
                "sweep_group_id": sweep.group_id,
                "run_ids": [j.run_id for j in jobs],
                "status": sweep.status,
            }
        )
    cfg = payload.get("config") or build_run_yaml(payload.get("workflow", {}))
    validate_run_yaml(cfg)
    job = submit_run(cfg, current_app.config["EXPERIMENTS_DIR"])
    return jsonify({"run_id": job.run_id, "status": job.status})


@bp.get("/sweeps")
def list_sweeps():
    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    limit = min(int(request.args.get("limit", 40)), 100)
    history = list_sweep_history(experiments_dir, limit=limit)
    return jsonify({"sweeps": [h.to_dict() for h in history], "count": len(history)})


@bp.get("/sweeps/resolve")
def resolve_sweep():
    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    query = request.args.get("q", "")
    group_id = resolve_group_id(experiments_dir, query)
    if group_id is None:
        return jsonify({"query": query, "group_id": None, "found": False}), 404
    sweep = get_sweep_group(group_id, experiments_dir=experiments_dir)
    return jsonify(
        {
            "query": query,
            "group_id": group_id,
            "found": True,
            "status": sweep.status if sweep else "unknown",
            "url": f"/sweep/{group_id}",
        }
    )


@bp.get("/sweeps/<group_id>")
def sweep_status(group_id: str):
    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    sweep = get_sweep_group(group_id, experiments_dir=experiments_dir)
    if sweep is None:
        return jsonify({"error": "not found"}), 404

    runs = []
    for run_id in sweep.run_ids:
        job = get_job(run_id, experiments_dir=experiments_dir)
        if job is None:
            continue
        runs.append(
            {
                "run_id": job.run_id,
                "name": job.meta.get("name", job.run_id[:8]),
                "status": job.status,
                "position": job.position,
                "error": job.error,
            }
        )

    completed = sum(1 for r in runs if r["status"] == "completed")
    failed = sum(1 for r in runs if r["status"] == "failed")
    active = sum(1 for r in runs if r["status"] in ("queued", "running"))

    return jsonify(
        {
            "group_id": sweep.group_id,
            "status": sweep.status,
            "current_index": sweep.current_index,
            "total": sweep.total,
            "completed": completed,
            "failed": failed,
            "active": active,
            "runs": runs,
            "error": sweep.error,
        }
    )


@bp.get("/runs/<run_id>")
def run_status(run_id: str):
    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    job = get_job(run_id, experiments_dir=experiments_dir)
    run_dir = experiments_dir / run_id
    summary_path = run_dir / "results" / "summary.json"

    if job is None and not run_dir.exists():
        return jsonify({"error": "not found"}), 404

    status = job.status if job else "unknown"
    if summary_path.exists() and status not in ("failed",):
        status = "completed"

    body = {"run_id": run_id, "status": status}
    if job:
        body["position"] = job.position
        body["sweep_group_id"] = job.sweep_group_id
    if job and job.error:
        body["error"] = job.error
    if summary_path.exists():
        body["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    return jsonify(body)
