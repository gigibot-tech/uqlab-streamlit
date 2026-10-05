"""5-step workflow wizard (session-based)."""

from __future__ import annotations

import hashlib
import json
import secrets

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for

from uqlab_orchestrator.config import default_workflow, merge_workflow_defaults

bp = Blueprint("wizard", __name__)


def _workflow() -> dict:
    if "workflow" not in session:
        session["workflow"] = default_workflow()
    else:
        session["workflow"] = merge_workflow_defaults(session["workflow"])
    return session["workflow"]


def _workflow_fingerprint(wf: dict) -> str:
    payload = json.dumps(wf, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _issue_launch_token() -> str:
    token = secrets.token_hex(16)
    session["launch_token"] = token
    return token


@bp.route("/")
def index():
    return redirect(url_for("wizard.step", n=1))


@bp.route("/step/<int:n>", methods=["GET", "POST"])
def step(n: int):
    wf = _workflow()
    if request.method == "POST":
        _apply_step(n, wf, request.form)
        session["workflow"] = wf
        if n < 5:
            return redirect(url_for("wizard.step", n=n + 1))
        return redirect(url_for("wizard.review"))

    return render_template(
        f"step{n}.html",
        step=n,
        workflow=wf,
        datasets=["cifar10", "cifar10n", "mnist"],
    )


def _apply_step(n: int, wf: dict, form) -> None:
    if n == 1:
        wf["dataset_config"] = {
            "dataset_name": form.get("dataset_name", "cifar10"),
            "noise_type": form.get("noise_type", "clean_label"),
        }
        wf["step1_complete"] = True
    elif n == 2:
        wf["training_config"] = {
            "model_architecture": form.get("model_architecture", "resnet18"),
            "training_scope": form.get("training_scope", "full"),
            "hidden_dim": int(form.get("hidden_dim", 256)),
            "dropout": float(form.get("dropout", 0.0)),
            "epochs": int(form.get("epochs", 12)),
            "learning_rate": float(form.get("learning_rate", 0.001)),
            "batch_size": int(form.get("batch_size", 256)),
        }
        wf["step2_complete"] = True
    elif n == 3:
        wf["uncertainty_config"] = {
            "sweep_enabled": form.get("sweep_enabled") == "on",
            "sweep_kind": form.get("sweep_kind", "label_noise"),
            "sweep_mode": form.get("sweep_mode", "quick"),
            "epistemic_enabled": False,
            "aleatoric_enabled": True,
            "regular_train_per_class": 300,
            "under_supported": "random:2",
        }
        wf["step3_complete"] = True
    elif n == 4:
        wf["evaluation_config"] = {
            "eval_per_group": int(form.get("eval_per_group", 100)),
            "mc_passes": int(form.get("mc_passes", 10)),
        }
        wf["step4_complete"] = True
        wf["step5_complete"] = True


@bp.route("/review")
def review():
    return render_template(
        "review.html",
        workflow=_workflow(),
        launch_token=_issue_launch_token(),
    )


@bp.route("/launch", methods=["POST"])
def launch():
    from uqlab_flask.executor import get_sweep_group, submit_sweep, sweep_is_active

    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    token = request.form.get("launch_token")
    expected = session.pop("launch_token", None)

    # One-time token: blocks double-click and accidental POST replay.
    if not expected or token != expected:
        group_id = session.get("last_sweep_group_id")
        if group_id:
            return redirect(url_for("wizard.sweep_status", group_id=group_id))
        return redirect(url_for("wizard.review"))

    wf = _workflow()
    fingerprint = _workflow_fingerprint(wf)
    active_group_id = session.get("active_sweep_group_id")

    if session.get("workflow_fingerprint") == fingerprint and active_group_id:
        existing = get_sweep_group(active_group_id, experiments_dir=experiments_dir)
        if existing and sweep_is_active(existing):
            return redirect(url_for("wizard.sweep_status", group_id=active_group_id))

    sweep, jobs = submit_sweep(wf, experiments_dir)
    session["last_run_ids"] = [j.run_id for j in jobs]
    session["last_sweep_group_id"] = sweep.group_id
    session["workflow_fingerprint"] = fingerprint
    session["active_sweep_group_id"] = sweep.group_id
    return redirect(f"/sweep/{sweep.group_id}")


@bp.route("/launched")
def launched_legacy():
    group_id = session.get("last_sweep_group_id")
    if group_id:
        return redirect(url_for("wizard.sweep_status", group_id=group_id))
    return redirect("/sweeps")


@bp.route("/sweeps", endpoint="sweeps_hub")
def sweeps_hub():
    """History hub — pick or search a sweep group."""
    from uqlab_flask.executor import list_sweep_history, resolve_group_id

    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    query = request.args.get("q", "").strip()
    if query:
        group_id = resolve_group_id(experiments_dir, query)
        if group_id:
            return redirect(f"/sweep/{group_id}")

    history = list_sweep_history(experiments_dir, limit=100)
    return _render_sweep_page(
        group_id="",
        jobs=[],
        history=history,
        search_query=query,
        not_found=bool(query),
    )


@bp.route("/sweeps/list")
def sweeps_list_json():
    """JSON list for refresh — lives on wizard blueprint (no /api prefix)."""
    from uqlab_flask.executor import list_sweep_history

    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    limit = min(int(request.args.get("limit", 100)), 200)
    history = list_sweep_history(experiments_dir, limit=limit)
    return jsonify({"sweeps": [h.to_dict() for h in history], "count": len(history)})


def _render_sweep_page(
    *,
    group_id: str,
    jobs: list,
    history: list,
    search_query: str = "",
    not_found: bool = False,
):
    return render_template(
        "launched.html",
        jobs=jobs,
        group_id=group_id,
        history=[h.to_dict() for h in history],
        search_query=search_query,
        not_found=not_found,
    )


@bp.route("/sweep/<group_id>/status")
def sweep_status_json(group_id: str):
    from uqlab_flask.executor import get_job, get_sweep_group

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


@bp.route("/sweep/<group_id>/plot")
def sweep_plot_json(group_id: str):
    """3-line sweep plot data (signal means + accuracy); not AUROC."""
    from uqlab.evaluation.reporting.sweep_line_plot import build_sweep_line_plot
    from uqlab_flask.executor import get_sweep_group

    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    sweep = get_sweep_group(group_id, experiments_dir=experiments_dir)
    if sweep is None:
        return jsonify({"error": "not found"}), 404

    signal = request.args.get("signal") or None
    try:
        payload = build_sweep_line_plot(
            sweep.run_ids,
            experiments_dir,
            signal=signal,
        )
        return jsonify(payload.to_dict())
    except ValueError as exc:
        return jsonify({"error": str(exc), "group_id": group_id}), 400


@bp.route("/sweep/<group_id>")
def sweep_status(group_id: str):
    from uqlab_flask.executor import get_job, get_sweep_group, list_sweep_history

    experiments_dir = current_app.config["EXPERIMENTS_DIR"]
    sweep = get_sweep_group(group_id, experiments_dir=experiments_dir)
    if sweep is None:
        return render_template("sweep_not_found.html", group_id=group_id), 404

    jobs = []
    for run_id in sweep.run_ids:
        job = get_job(run_id, experiments_dir=experiments_dir)
        if job is not None:
            jobs.append(job)

    history = list_sweep_history(experiments_dir, limit=100)
    return _render_sweep_page(
        group_id=group_id,
        jobs=jobs,
        history=history,
    )
