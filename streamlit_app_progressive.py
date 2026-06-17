"""
Progressive Disclosure Streamlit App for Uncertainty Quantification
Inspired by MLflow UI pattern - each step appears only after previous is completed
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure uqlab package is importable (src/ on PYTHONPATH)
_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC = _PROJECT_ROOT / "src"
for _path in (_SRC, _PROJECT_ROOT):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import os

import pandas as pd
import requests
import streamlit as st

# Import from orchestrator (moved to break circular dependency)
from uqlab_orchestrator.experiment_config import (
    build_base_experiment_config,
    build_nested_experiment_config,
)

# Import orchestrator package for sweep generation
from uqlab_orchestrator import BatchGenerator, SweepType

# Add backend to path for domain models
import sys
_BACKEND = _PROJECT_ROOT / "backend"

# Import validation
try:
    from uqlab.shared.config.workflow_validation import (
        validate_workflow,
        get_validation_errors,
    )
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.domain.models import (
    ExperimentConfig,
    DataConfig,
    ModelConfig,
    TrainingRuntimeConfig,
    EvaluationConfig,
    PathsConfig,
)
from uqlab.ui_components.orchestration.validation_runner import (
    render_local_validation_viz,
    render_preset_validation_sweeps,
)
from uqlab.ui_components.results.experiment_results_panel import (
    render_experiment_results_panel,
    render_experiment_stats_footer,
)
from uqlab.ui_components.selectors.paper_sweep_launch import (
    build_paper_profile_workflow,
    new_campaign_timestamp,
    render_sidebar_paper_launch,
)
from uqlab.ui_components.selectors.sidebar_controls import render_sidebar_footer_debug
from uqlab.ui_components.ui_debug import init_ui_debug, sync_results_auto_refresh, ui_on

try:
    from uqlab_orchestrator.config.validation_config import (
        LABEL_NOISE_SWEEP,
        TRAINING_CONFIG,
        aligned_sweep_summary,
        aligned_under_train_sweep,
    )
except ImportError:
    LABEL_NOISE_SWEEP = {"quick": [0, 25, 50, 75, 100], "full": list(range(0, 101, 10))}
    TRAINING_CONFIG = {
        "quick": {"epochs": 2, "mc_passes": 10},
        "full": {"epochs": 10, "mc_passes": 30},
    }

    def aligned_under_train_sweep(mode: str) -> list[int]:
        return [25, 50, 100, 150, 200] if mode == "quick" else list(range(25, 801, 75))

    def aligned_sweep_summary(mode: str) -> dict:
        return {
            "label_noise_percent": LABEL_NOISE_SWEEP[mode],
            "under_train_per_class": aligned_under_train_sweep(mode),
        }

# Recommended defaults: fast label-noise sweep (same points as Hypothesis Validation quick).
DEFAULT_WORKFLOW: Dict[str, Any] = {
    "step1_complete": True,
    "step2_complete": True,
    "step3_complete": True,
    "step4_complete": True,
    "dataset_config": {
        "dataset_name": "cifar10",
        "noise_type": "clean_label",
        "stats": {
            "total_samples": 50_000,
            "num_classes": 10,
            "noise_rate": 0.4,
        },
    },
    "training_config": {
        "use_checkpoint": False,
        "model_architecture": "resnet18",
        "hidden_dim": 256,
        "dropout": 0.0,
        "epochs": TRAINING_CONFIG["quick"]["epochs"],
        "learning_rate": 0.001,
        "batch_size": 256,
    },
    "uncertainty_config": {
        "epistemic_enabled": False,
        "under_supported": "random:2",
        "under_train_per_class": 50,
        "regular_train_per_class": 300,
        "aleatoric_enabled": True,
        "custom_noise_rate": None,
        "sweep_enabled": True,
        "sweep_kind": "label_noise",
        "sweep_mode": "quick",
        "epistemic_sweep_enabled": False,
        "epistemic_sweep_values": [25, 50, 100, 150, 200],
        "aleatoric_sweep_enabled": True,
        "aleatoric_sweep_values": LABEL_NOISE_SWEEP["quick"],
    },
    "evaluation_config": {
        "eval_per_group": 100,
        "mc_passes": TRAINING_CONFIG["quick"]["mc_passes"],
        "selected_signals": [
            "inverse_mass",
            "dominance",
            "inverse_logit_magnitude",
            "inverse_coherence",
            "msp_uncertainty",
            "predictive_entropy",
            "mutual_info",
        ],
    },
}


def _empty_workflow() -> Dict[str, Any]:
    return {
        "step1_complete": False,
        "step2_complete": False,
        "step3_complete": False,
        "step4_complete": False,
        "dataset_config": {},
        "training_config": {},
        "uncertainty_config": {},
        "evaluation_config": {},
    }


def _default_workflow() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULT_WORKFLOW)


CIFAR10N_NOISE_OPTIONS = (
    "clean_label",
    "worse_label",
    "aggre_label",
    "random_label1",
    "random_label2",
    "random_label3",
)

DATASET_CATALOG: Dict[str, Dict[str, str]] = {
    "cifar10": {
        "label": "CIFAR-10 (original)",
        "short": "CIFAR-10",
        "description": (
            "Standard torchvision CIFAR-10 — **clean, verified labels**. "
            "Paper sweeps (Fig. 3/4) inject synthetic label noise at train time."
        ),
    },
    "cifar10n": {
        "label": "CIFAR-10N (human noisy labels)",
        "short": "CIFAR-10N",
        "description": (
            "Same 50k images as CIFAR-10, but labels come from **human annotators** "
            "(Wei et al.). Choose a noise split below — not the same as synthetic sweep noise."
        ),
    },
}

CIFAR10N_NOISE_LABELS: Dict[str, str] = {
    "clean_label": "Clean labels (baseline — matches CIFAR-10)",
    "worse_label": "Worse label (~40% noisy)",
    "aggre_label": "Aggregate label (~9% noisy)",
    "random_label1": "Random label 1 (~20% noisy)",
    "random_label2": "Random label 2 (~20% noisy)",
    "random_label3": "Random label 3 (~20% noisy)",
}


def _is_clean_noise(noise_type: str) -> bool:
    return noise_type in ("none", "clean_label", "clean", "no_noise")


def _fallback_dataset_stats(dataset_name: str, noise_type: str) -> dict:
    """Offline stats when the FastAPI backend is not running."""
    if dataset_name == "cifar10":
        return {
            "total_samples": 50_000,
            "num_classes": 10,
            "noise_rate": 0.0,
            "dataset_name": "cifar10",
            "noise_type": "clean_label",
            "source": "fallback",
        }
    noise_rates = {
        "none": 0.0,
        "clean_label": 0.0,
        "worse_label": 0.4021,
        "aggre_label": 0.09,
        "random_label1": 0.2,
        "random_label2": 0.2,
        "random_label3": 0.2,
    }
    return {
        "total_samples": 50_000,
        "num_classes": 10,
        "noise_rate": noise_rates.get(noise_type, 0.0),
        "dataset_name": "cifar10n",
        "noise_type": noise_type,
        "source": "fallback",
    }


def _merge_workflow_defaults(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Backfill sweep keys for older session state (Streamlit reruns)."""
    defaults = _default_workflow()
    for key in ("dataset_config", "training_config", "uncertainty_config", "evaluation_config"):
        if key not in workflow or not isinstance(workflow.get(key), dict):
            workflow[key] = copy.deepcopy(defaults[key])
        else:
            for sub_key, sub_val in defaults[key].items():
                workflow[key].setdefault(sub_key, copy.deepcopy(sub_val) if isinstance(sub_val, list) else sub_val)
    for flag in ("step1_complete", "step2_complete", "step3_complete", "step4_complete"):
        workflow.setdefault(flag, defaults.get(flag, False))
    uc = workflow.get("uncertainty_config", {})
    if uc.get("sweep_enabled") and uc.get("sweep_kind", "label_noise") == "label_noise":
        workflow.setdefault("dataset_config", {})
        workflow["dataset_config"]["noise_type"] = "clean_label"
    return workflow


def _ensure_workflow_initialized() -> None:
    if "workflow" not in st.session_state:
        st.session_state.workflow = _default_workflow()
    else:
        st.session_state.workflow = _merge_workflow_defaults(st.session_state.workflow)
    if "launch_result" not in st.session_state:
        st.session_state.launch_result = None
    if "results_auto_refresh" not in st.session_state:
        st.session_state.results_auto_refresh = False
    if "highlight_experiment_id" not in st.session_state:
        st.session_state.highlight_experiment_id = None
    if "experiment_selection_in_sidebar" not in st.session_state:
        st.session_state.experiment_selection_in_sidebar = True
    init_ui_debug()
    sync_results_auto_refresh()


def _normalize_dinov2_model(architecture_label: str) -> str:
    """API expects ``small`` / ``base``, not ``dinov2-small``."""
    label = (architecture_label or "dinov2-small").strip()
    if label.startswith("dinov2-"):
        return label.split("dinov2-", 1)[1]
    if label.startswith("dinov2_"):
        return label.split("dinov2_", 1)[1]
    return label


def _sweep_mode(workflow: Dict[str, Any]) -> str:
    return workflow.get("uncertainty_config", {}).get("sweep_mode", "quick")


def _workflow_to_experiment_config(
    workflow: Dict[str, Any],
    *,
    under_train_per_class: Optional[int] = None,
    aleatoric_noise_percentage: Optional[float] = None,
) -> ExperimentConfig:
    """Convert workflow dict to typed ExperimentConfig."""
    training = workflow["training_config"]
    uncertainty = workflow["uncertainty_config"]
    evaluation = workflow["evaluation_config"]
    dataset = workflow["dataset_config"]
    dataset_name = dataset.get("dataset_name", "cifar10")
    noise_type_in = dataset.get("noise_type", "clean_label")
    
    epistemic_on = bool(uncertainty.get("epistemic_enabled", False))
    regular = uncertainty.get("regular_train_per_class") or 300
    under_supported = uncertainty.get("under_supported") or (
        "random:2" if epistemic_on else "random:1"
    )

    if under_train_per_class is not None:
        under = int(under_train_per_class)
    elif epistemic_on:
        raw_under = uncertainty.get("under_train_per_class")
        under = int(raw_under) if raw_under is not None else 50
    else:
        # Aleatoric-only: balanced training (equal samples per class)
        # Ensure regular is not None before converting to int
        under = int(regular) if regular is not None else 300
    
    # Calculate aleatoric noise percentage with proper validation
    use_cifar10n_native_noise = (
        dataset_name == "cifar10n"
        and not _is_clean_noise(noise_type_in)
    )

    if aleatoric_noise_percentage is not None:
        alea_pct: Optional[float] = float(aleatoric_noise_percentage)
    elif use_cifar10n_native_noise and uncertainty.get("aleatoric_enabled", False):
        # Let training script load CIFAR-10N human noise from noise_type.
        alea_pct = None
    else:
        aleatoric_enabled = uncertainty.get("aleatoric_enabled", False)
        custom_noise = uncertainty.get("custom_noise_rate")

        if not aleatoric_enabled:
            alea_pct = 0.0
        elif custom_noise is not None:
            alea_pct = float(custom_noise) * 100.0
        elif not _is_clean_noise(noise_type_in):
            stats = dataset.get("stats", {})
            dataset_noise_rate = stats.get("noise_rate", 0.0)
            alea_pct = float(dataset_noise_rate) * 100.0
        else:
            alea_pct = 0.0

    if dataset_name == "cifar10" or _is_clean_noise(noise_type_in):
        noise_type_out = "clean_label"
    elif use_cifar10n_native_noise and alea_pct is None:
        noise_type_out = noise_type_in
    elif alea_pct is not None and alea_pct > 0:
        # Synthetic injection from clean base (paper Fig. 4 sweeps).
        noise_type_out = "clean_label"
    else:
        noise_type_out = noise_type_in
    
    # Determine architecture from model selection
    model_arch = training.get("model_architecture", "resnet18")
    if "resnet" in model_arch.lower():
        architecture = "resnet18_mcdropout"
        dinov2_model = "small"  # Not used for ResNet
    else:
        architecture = "dinov2_mlp"
        dinov2_model = _normalize_dinov2_model(model_arch)
    
    return ExperimentConfig(
        seed=42,
        device="auto",
        data=DataConfig(
            noise_type=noise_type_out,
            under_supported_classes=under_supported,
            under_train_per_class=under,
            regular_train_per_class=regular,
            aleatoric_noise_percentage=alea_pct,
            eval_per_group=evaluation["eval_per_group"],
        ),
        model=ModelConfig(
            architecture=architecture,
            dinov2_model=dinov2_model,
            hidden_dim=training.get("hidden_dim", 256),
            dropout=training.get("dropout", 0.0),
            use_untrained_resnet=False,
        ),
        training=TrainingRuntimeConfig(
            epochs=training.get("epochs", 12),
            learning_rate=training.get("learning_rate", 0.001),
            weight_decay=0.0001,
            train_batch_size=training.get("batch_size", 256),
        ),
        evaluation=EvaluationConfig(
            mc_passes=evaluation.get("mc_passes", 0),
        ),
        paths=PathsConfig(),
    )


def _generate_sweep_configs(workflow: Dict[str, Any]) -> Tuple[SweepType, List[ExperimentConfig]]:
    """Generate sweep configs using BatchGenerator."""
    base_config = _workflow_to_experiment_config(workflow)
    generator = BatchGenerator()
    
    u = workflow["uncertainty_config"]
    mode = _sweep_mode(workflow)
    
    if not u.get("sweep_enabled", True):
        return SweepType.SINGLE_POINT, [base_config]
    
    kind = u.get("sweep_kind", "label_noise")
    
    if kind == "dataset_size" and u.get("epistemic_sweep_enabled", True):
        values = u.get("epistemic_sweep_values") or aligned_under_train_sweep(mode)
        configs = generator.generate_epistemic_sweep(base_config, values)
        return SweepType.EPISTEMIC_1D, configs
    
    if kind == "label_noise" and u.get("aleatoric_sweep_enabled", True):
        values = u.get("aleatoric_sweep_values") or LABEL_NOISE_SWEEP.get(mode, LABEL_NOISE_SWEEP["quick"])
        configs = generator.generate_aleatoric_sweep(base_config, values)
        return SweepType.ALEATORIC_1D, configs
    
    return SweepType.SINGLE_POINT, [base_config]


def _launch_workflow_experiments(
    workflow: Dict[str, Any],
    *,
    auto_start: bool,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate configs using BatchGenerator and submit to API."""
    sweep_type, configs = _generate_sweep_configs(workflow)
    timestamp = timestamp or pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    created_runs: List[Dict[str, Any]] = []
    errors: List[str] = []
    
    for i, config in enumerate(configs):
        # Generate name based on sweep type
        if sweep_type == SweepType.ALEATORIC_1D:
            alea_val = config.data.aleatoric_noise_percentage or 0.0
            name = f"fast_alea_{timestamp}_noise_{int(alea_val)}"
        elif sweep_type == SweepType.EPISTEMIC_1D:
            name = f"fast_epis_{timestamp}_under_{config.data.under_train_per_class}"
        else:
            name = f"exp_{timestamp}"
        
        try:
            # Submit to API
            payload = {"name": name, "config": config.model_dump()}
            create_resp = requests.post(
                f"{API_BASE_URL}/api/v1/experiments/no-auth",
                json=payload,
                headers=get_headers(),
                timeout=30,
            )
            create_resp.raise_for_status()
            created = create_resp.json()
            exp_id = str(created["id"])
            
            # Auto-start if requested
            started = False
            start_error: Optional[str] = None
            if auto_start:
                try:
                    start_resp = requests.post(
                        f"{API_BASE_URL}/api/v1/experiments/no-auth/{exp_id}/start",
                        headers=get_headers(),
                        timeout=30,
                    )
                    start_resp.raise_for_status()
                    started = True
                except requests.exceptions.RequestException as exc:
                    start_error = str(exc)
                    if hasattr(exc, "response") and exc.response is not None:
                        start_error = f"{exc}\n{exc.response.text}"
            
            created_runs.append({
                "id": exp_id,
                "name": name,
                "started": started,
                "start_error": start_error,
                "config": config,
                "under_train": config.data.under_train_per_class,
                "aleatoric_noise_percentage": config.data.aleatoric_noise_percentage,
            })
        except requests.exceptions.RequestException as exc:
            detail = exc.response.text if hasattr(exc, "response") and exc.response is not None else ""
            errors.append(f"{name}: {exc}\n{detail}")
    
    if not created_runs:
        return {"ok": False, "error": "No experiments created", "detail": "\n".join(errors)}
    
    st.session_state.highlight_experiment_id = created_runs[-1]["id"]
    n_started = sum(1 for r in created_runs if r.get("started"))
    n_failed_start = sum(1 for r in created_runs if r.get("start_error"))
    
    return {
        "ok": True,
        "sweep_axis": sweep_type.value,  # Use SweepType enum value
        "n_created": len(created_runs),
        "n_started": n_started,
        "n_failed_start": n_failed_start,
        "created_runs": created_runs,
        "errors": errors,
        "created": created_runs[-1],
        "experiment_id": created_runs[-1]["id"],
        "started": n_started == len(created_runs),
        "start_error": created_runs[-1].get("start_error") if n_failed_start else None,
        "campaign_timestamp": timestamp,
    }


def _merge_launch_results(
    *results: Dict[str, Any],
    sweep_axis: str = "paired",
    campaign_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Combine multiple launch results (e.g. Fig. 3 + Fig. 4 arms)."""
    created_runs: List[Dict[str, Any]] = []
    errors: List[str] = []
    for res in results:
        if res.get("created_runs"):
            created_runs.extend(res["created_runs"])
        if res.get("errors"):
            errors.extend(res["errors"])

    if not created_runs:
        failed = [r for r in results if not r.get("ok")]
        detail = "\n".join(
            f"{r.get('error', 'unknown')}: {r.get('detail', '')}" for r in failed
        )
        return {"ok": False, "error": "No experiments created", "detail": detail or None}

    st.session_state.highlight_experiment_id = created_runs[-1]["id"]
    n_started = sum(1 for r in created_runs if r.get("started"))
    n_failed_start = sum(1 for r in created_runs if r.get("start_error"))

    return {
        "ok": True,
        "sweep_axis": sweep_axis,
        "n_created": len(created_runs),
        "n_started": n_started,
        "n_failed_start": n_failed_start,
        "created_runs": created_runs,
        "errors": errors,
        "created": created_runs[-1],
        "experiment_id": created_runs[-1]["id"],
        "started": n_started == len(created_runs),
        "start_error": created_runs[-1].get("start_error") if n_failed_start else None,
        "campaign_timestamp": campaign_timestamp,
    }


def _paper_workflow(workflow: Dict[str, Any], profile: str) -> Dict[str, Any]:
    mode = _sweep_mode(workflow)
    return build_paper_profile_workflow(
        workflow,
        profile,
        mode,
        under_train_sweep=aligned_under_train_sweep,
        label_noise_sweep=LABEL_NOISE_SWEEP,
    )


def _launch_paper_profile(
    workflow: Dict[str, Any],
    profile: str,
    *,
    auto_start: bool,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    paper = _paper_workflow(workflow, profile)
    return _launch_workflow_experiments(
        paper,
        auto_start=auto_start,
        timestamp=timestamp or new_campaign_timestamp(),
    )


def _launch_paired_paper_profiles(
    workflow: Dict[str, Any],
    *,
    auto_start: bool,
) -> Dict[str, Any]:
    ts = new_campaign_timestamp()
    epis = _launch_paper_profile(workflow, "under_train", auto_start=auto_start, timestamp=ts)
    alea = _launch_paper_profile(workflow, "noise", auto_start=auto_start, timestamp=ts)
    return _merge_launch_results(epis, alea, sweep_axis="paired_fig3_fig4", campaign_timestamp=ts)


def _render_progressive_results_section() -> None:
    """API results + sweep grouping (gated by UI debug)."""
    if not ui_on("results_section"):
        sync_results_auto_refresh()
        return

    # Wrap local preset sweeps in legacy expander
    if ui_on("results_local_presets") or ui_on("results_local_viz"):
        with st.expander("📦 Legacy: Local Preset Sweeps (Fig. 3 / Fig. 4)", expanded=False):
            st.caption("⚠️ **Legacy view** - Local validation preset sweeps from disk artifacts")
            
            if ui_on("results_local_presets"):
                st.markdown("#### Launch Preset Sweeps")
                render_preset_validation_sweeps(key_prefix="prog_preset", show_viz=False)
            
            if ui_on("results_local_viz"):
                st.markdown("#### Validation Visualizations")
                # These are local preset sweep plots read from `results/validation/*/metrics.csv`.
                # Always show both Fig. 3 (dataset_size) and Fig. 4 (label_noise) if data exists.
                show_fig3 = True
                show_fig4 = True

                model_arch = st.session_state.get("workflow", {}).get("training_config", {}).get(
                    "model_architecture", "resnet18"
                )
                architecture_label = "DINOv2 + MLP"
                if model_arch and "resnet" in str(model_arch).lower():
                    architecture_label = "ResNet18 MC Dropout"

                render_local_validation_viz(
                    key_prefix="prog_preset_viz",
                    show_fig3=show_fig3,
                    show_fig4=show_fig4,
                    architecture_label=architecture_label,
                )

    st.markdown("---")
    st.markdown("### 📊 Experiment results & progress")

    st.session_state.results_auto_refresh = render_experiment_results_panel(
        API_BASE_URL,
        get_headers,
        st.session_state.results_auto_refresh,
        caption=(
            f"Live data from `{API_BASE_URL}`. "
            "Enable auto-refresh while a run is **running**."
        ),
        empty_message=(
            "No experiments in the database yet. Use **Paper sweeps** in the sidebar."
        ),
        highlight_experiment_id=st.session_state.get("highlight_experiment_id"),
        key_prefix="prog_",
        detail_mode="select",
        show_batch_visualizations=True,
        show_signal_sweep_plots=True,
        workflow=st.session_state.workflow,
        show_experiment_selection=not st.session_state.get(
            "experiment_selection_in_sidebar", True
        ),
        show_launch_controls=False,
    )


def _render_launch_result() -> None:
    """Show last launch outcome (persists across Streamlit reruns)."""
    if not ui_on("launch_result_banner"):
        return
    result = st.session_state.get("launch_result")
    if not result:
        return

    if not result.get("ok"):
        st.error(f"Launch failed: {result.get('error', 'Unknown error')}")
        if result.get("detail"):
            with st.expander("Error details"):
                st.code(result["detail"])
        return

    n = result.get("n_created", 1)
    axis = result.get("sweep_axis", "single")
    if n > 1:
        st.success(f"**Fast sweep launched:** {n} experiments ({axis}).")
        if result.get("errors"):
            st.warning("Some points failed to create — see details below.")
            with st.expander("Creation errors"):
                st.code("\n".join(result["errors"]))
        with st.expander("Created runs", expanded=False):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "name": r["name"],
                            "id": r["id"],
                            "under_train": r.get("under_train"),
                            "noise_%": r.get("aleatoric_noise_percentage"),
                            "started": r.get("started"),
                        }
                        for r in result.get("created_runs", [])
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
    else:
        created = result["created"]
        st.success(f"Experiment **{created.get('name', '?')}** created (ID `{result['experiment_id']}`).")

    if result.get("n_started", 0) == n and n > 0:
        st.info(
            "Training started for all runs. Use **Experiment Results & Progress** above "
            "(enable auto-refresh), then select any run in the batch to see paper-style sweep plots."
        )
    elif result.get("n_failed_start"):
        st.warning(
            f"{result['n_failed_start']} run(s) failed to start — use **Queued → Start** above "
            "or fix the backend error."
        )
        if result.get("start_error"):
            st.code(result["start_error"])
    elif not result.get("started"):
        st.info("Experiments saved **without** starting training (checkbox was off).")

# Page config
st.set_page_config(
    page_title="UQ Experiment Builder",
    page_icon="🔬",
    layout="wide"
)

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")

# Custom CSS for progressive disclosure
st.markdown("""
<style>
.step-complete {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
    padding: 12px;
    border-radius: 4px;
    margin: 10px 0;
}

.step-active {
    background-color: rgba(33, 150, 243, 0.1);
    border-left: 4px solid #2196F3;
    padding: 20px;
    border-radius: 4px;
    margin: 10px 0;
}

.step-pending {
    opacity: 0.5;
    padding: 12px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


def selectbox_without_default(label, options, help_text=None):
    """Selectbox that requires explicit selection (no default)"""
    options_with_empty = [''] + list(options)
    format_func = lambda x: '⬇️ Select one option' if x == '' else x
    return st.selectbox(label, options_with_empty, format_func=format_func, help=help_text)


def get_headers() -> dict:
    """Get request headers with optional authentication"""
    headers = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


def fetch_dataset_stats(
    dataset_name: str,
    noise_type: str,
    *,
    quiet: bool = False,
) -> dict:
    """Fetch dataset statistics from the backend API, with offline fallback."""
    try:
        url = f"{API_BASE_URL}/api/v1/datasets/{dataset_name}/stats"
        params = {"noise_type": noise_type}
        response = requests.get(url, params=params, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if not quiet:
            st.warning(
                f"Backend unavailable ({e}). Using offline dataset stats for the UI."
            )
        return _fallback_dataset_stats(dataset_name, noise_type)


def main():
    if ui_on("page_title"):
        st.title("🔬 Uncertainty Quantification Experiment Builder")
        st.caption(
            "Configure Steps 1–4, launch paper sweeps from the **sidebar**, "
            "view **results** below."
        )

    _ensure_workflow_initialized()
    workflow = st.session_state.workflow

    with st.sidebar:
        render_sidebar_paper_launch(
            workflow,
            on_launch_both=lambda auto: _launch_paired_paper_profiles(
                workflow, auto_start=auto
            ),
            on_launch_epis=lambda auto: _launch_paper_profile(
                workflow, "under_train", auto_start=auto
            ),
            on_launch_alea=lambda auto: _launch_paper_profile(
                workflow, "noise", auto_start=auto
            ),
            aligned_sweep_summary=aligned_sweep_summary,
        )
        render_sidebar_footer_debug()

    _render_launch_result()
    
    # ========== STEP 1: DATASET SELECTION ==========
    if not ui_on("step1_dataset"):
        pass
    elif workflow['step1_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            dataset_name = workflow['dataset_config']['dataset_name']
            noise_type = workflow['dataset_config'].get('noise_type', 'clean_label')
            ds_label = DATASET_CATALOG.get(dataset_name, {}).get("short", dataset_name.upper())
            if dataset_name == "cifar10n":
                noise_label = CIFAR10N_NOISE_LABELS.get(noise_type, noise_type)
                st.markdown(f"**✅ Step 1: Dataset** — {ds_label} · {noise_label}")
            else:
                st.markdown(f"**✅ Step 1: Dataset** — {ds_label} (clean labels)")
        with col2:
            if st.button("Edit", key="edit_step1"):
                workflow['step1_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 1: Dataset Selection")
        
        dataset_ids = list(DATASET_CATALOG.keys())
        saved_ds = workflow["dataset_config"].get("dataset_name", "cifar10")
        ds_index = dataset_ids.index(saved_ds) if saved_ds in dataset_ids else 0
        dataset_choice = st.selectbox(
            "Choose a dataset",
            dataset_ids,
            index=ds_index,
            format_func=lambda k: DATASET_CATALOG[k]["label"],
            help="CIFAR-10 = clean torchvision labels. CIFAR-10N = same images with human noisy labels.",
        )
        st.caption(DATASET_CATALOG[dataset_choice]["description"])

        if dataset_choice == "cifar10":
            noise_choice = "clean_label"
            st.info(
                "ℹ️ **CIFAR-10 (original)** uses clean labels only. "
                "Label noise for Fig. 4 sweeps is injected synthetically in Step 3 — "
                "no CIFAR-10N split needed."
            )
        else:
            noise_options = list(CIFAR10N_NOISE_OPTIONS)
            saved_noise = workflow["dataset_config"].get("noise_type", "worse_label")
            if saved_noise == "none":
                saved_noise = "worse_label"
            default_noise_idx = (
                noise_options.index(saved_noise)
                if saved_noise in noise_options
                else noise_options.index("worse_label")
            )
            noise_choice = st.selectbox(
                "CIFAR-10N noise split",
                noise_options,
                index=default_noise_idx,
                format_func=lambda k: CIFAR10N_NOISE_LABELS.get(k, k),
                help="Human-annotated label noise from the CIFAR-10N benchmark (Wei et al.).",
            )
            if _is_clean_noise(noise_choice):
                st.caption("Clean split — equivalent to CIFAR-10 labels on the same images.")
            else:
                st.caption(
                    "Training/eval will use the selected human-noise split. "
                    "For paper-style synthetic sweeps, pick **CIFAR-10 (original)** instead."
                )
        
        # Fetch and display stats
        with st.spinner("Loading dataset statistics..."):
            stats = fetch_dataset_stats(dataset_choice, noise_choice)
        
        if stats:
            if stats.get("source") == "fallback":
                st.caption("Using offline stats (start FastAPI backend for live numbers).")
            st.markdown("#### Dataset Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Samples", f"{stats.get('total_samples', 50000):,}")
            with col2:
                st.metric("Classes", stats.get('num_classes', 10))
            with col3:
                noise_rate = stats.get('noise_rate', 0.0)
                st.metric(
                    "Noise Rate",
                    f"{noise_rate:.1%}" if not _is_clean_noise(noise_choice) else "0%",
                )
            
            # Show dataset preview
            with st.expander("📋 View dataset details"):
                st.json(stats)
            
            # Continue button
            if st.button("✓ Continue to Training Setup", type="primary", use_container_width=True):
                workflow['step1_complete'] = True
                workflow['dataset_config'] = {
                    'dataset_name': dataset_choice,
                    'noise_type': noise_choice,
                    'stats': stats
                }
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()  # Don't show next steps until this is complete
    
    # ========== STEP 2: TRAINING SETUP ==========
    if not ui_on("step2_training"):
        pass
    elif workflow['step2_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            if workflow['training_config'].get('use_checkpoint'):
                checkpoint_id = workflow['training_config']['checkpoint_id']
                st.markdown(f"**✅ Step 2: Training** - Using checkpoint: {checkpoint_id}")
            else:
                model_arch = workflow['training_config']['model_architecture']
                epochs = workflow['training_config']['epochs']
                st.markdown(f"**✅ Step 2: Training** - {model_arch}, {epochs} epochs")
        with col2:
            if st.button("Edit", key="edit_step2"):
                workflow['step2_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🧠 Step 2: Training Setup")
        
        # Training mode selection
        training_mode = st.radio(
            "Training mode",
            ["Train new model", "Use existing checkpoint"],
            help="Train a new model or load a pre-trained checkpoint"
        )
        
        if training_mode == "Train new model":
            st.markdown("#### Model Configuration")
            
            col1, col2 = st.columns(2)
            with col1:
                arch_options = ["dinov2-small", "dinov2-base", "resnet18", "resnet50"]
                saved_arch = workflow["training_config"].get("model_architecture", "resnet18")
                arch_index = (
                    arch_options.index(saved_arch) if saved_arch in arch_options else 2
                )
                model_arch = st.selectbox(
                    "Model architecture",
                    arch_options,
                    index=arch_index,
                    help="DINOv2 models are pre-trained vision transformers",
                )
                hidden_dim = st.number_input(
                    "Hidden dimension",
                    min_value=64,
                    max_value=1024,
                    value=workflow["training_config"].get("hidden_dim", 256),
                    step=64,
                )
                saved_dropout = float(workflow["training_config"].get("dropout", 0.0))
                dropout = st.slider("Dropout rate", 0.0, 0.5, saved_dropout, 0.05)
            
            with col2:
                epochs = st.number_input("Training epochs", min_value=1, max_value=100, value=12)
                learning_rate = st.number_input("Learning rate", min_value=0.0001, max_value=0.1, value=0.001, format="%.4f")
                batch_size = st.selectbox("Batch size", [64, 128, 256, 512], index=2)
            
            if st.button("✓ Continue to Uncertainty Configuration", type="primary", use_container_width=True):
                workflow['step2_complete'] = True
                workflow['training_config'] = {
                    'use_checkpoint': False,
                    'model_architecture': model_arch,
                    'hidden_dim': hidden_dim,
                    'dropout': dropout,
                    'epochs': epochs,
                    'learning_rate': learning_rate,
                    'batch_size': batch_size
                }
                st.rerun()
        
        else:  # Use existing checkpoint
            st.markdown("#### Select Checkpoint")
            
            # Fetch available checkpoints
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/v1/experiments/no-auth",
                    headers=get_headers(),
                    timeout=10
                )
                response.raise_for_status()
                experiments = response.json()
                
                # Filter completed experiments
                completed_exps = [
                    exp for exp in experiments 
                    if exp.get('status') == 'completed'
                ]
                
                if completed_exps:
                    checkpoint_options = [
                        f"{exp['name']} (ID: {exp['id']})" 
                        for exp in completed_exps
                    ]
                    checkpoint_choice = selectbox_without_default(
                        "Select checkpoint",
                        checkpoint_options,
                        help_text="Choose a completed experiment to use as checkpoint"
                    )
                    
                    if checkpoint_choice:
                        # Extract experiment ID
                        checkpoint_id = checkpoint_choice.split("ID: ")[1].rstrip(")")
                        
                        if st.button("✓ Continue to Uncertainty Configuration", type="primary", use_container_width=True):
                            workflow['step2_complete'] = True
                            workflow['training_config'] = {
                                'use_checkpoint': True,
                                'checkpoint_id': checkpoint_id
                            }
                            st.rerun()
                    else:
                        st.info("👆 Please select a checkpoint to continue")
                else:
                    st.warning("No completed experiments found. Please train a new model.")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch experiments: {str(e)}")
                st.info("Falling back to training new model...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 3: UNCERTAINTY CONFIGURATION ==========
    if not ui_on("step3_uncertainty"):
        pass
    elif workflow['step3_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            uc = workflow["uncertainty_config"]
            sweep_on = uc.get("sweep_enabled", False)
            kind = uc.get("sweep_kind", "label_noise")
            mode = uc.get("sweep_mode", "quick")
            if sweep_on:
                n_pts = len(
                    uc.get("aleatoric_sweep_values") or LABEL_NOISE_SWEEP.get(mode, [])
                    if kind == "label_noise"
                    else uc.get("epistemic_sweep_values") or aligned_under_train_sweep(mode)
                )
                st.markdown(
                    f"**✅ Step 3: Uncertainty** — **fast {kind} sweep** "
                    f"({mode}, {n_pts} points)"
                )
            else:
                st.markdown(
                    f"**✅ Step 3: Uncertainty** — single point "
                    f"(epistemic={uc.get('epistemic_enabled')}, aleatoric={uc.get('aleatoric_enabled')})"
                )
        with col2:
            if st.button("Edit", key="edit_step3"):
                workflow['step3_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🎲 Step 3: Uncertainty Configuration")
        
        st.info("""
        **Understanding Uncertainty Types:**
        - **Fig. 3 (Dataset Size Sweep)**: Varies training data per class to measure **epistemic uncertainty** (model uncertainty from limited data)
        - **Fig. 4 (Label Noise Sweep)**: Varies label noise percentage to measure **aleatoric uncertainty** (data uncertainty from noisy labels)
        """)

        st.markdown("#### Fast sweep (default — same as Hypothesis Validation quick)")
        sweep_enabled = st.checkbox(
            "Launch a parameter sweep (recommended)",
            value=workflow["uncertainty_config"].get("sweep_enabled", True),
            help="Creates multiple API experiments so paper-style plots have an x-axis.",
        )
        sweep_kind = st.radio(
            "Sweep type",
            ["label_noise", "dataset_size"],
            index=0 if workflow["uncertainty_config"].get("sweep_kind", "label_noise") == "label_noise" else 1,
            horizontal=True,
            help="Label noise (Fig. 4) = aleatoric sweep. Dataset size (Fig. 3) = epistemic sweep.",
        )
        sweep_mode = st.radio(
            "Sweep mode",
            ["quick", "full"],
            index=0 if workflow["uncertainty_config"].get("sweep_mode", "quick") == "quick" else 1,
            horizontal=True,
            help=f"Quick: noise {LABEL_NOISE_SWEEP['quick']}; under-train {aligned_under_train_sweep('quick')}",
        )
        if sweep_enabled:
            if sweep_kind == "label_noise":
                st.caption(f"Will run **{len(LABEL_NOISE_SWEEP[sweep_mode])}** label-noise levels: {LABEL_NOISE_SWEEP[sweep_mode]}")
                st.info(
                    "**Fig. 4 (aleatoric):** Sweep **overrides** any noise settings below with the grid values above. "
                    "Epistemic is auto-disabled. For paired Fig. 3 + Fig. 4, use **Paper sweeps** in the sidebar."
                )
            else:
                vals = aligned_under_train_sweep(sweep_mode)
                st.caption(f"Will run **{len(vals)}** under-train sizes: {vals}")
                st.info(
                    "**Fig. 3 (epistemic):** Sweep **overrides** any under-training settings below with the grid values above. "
                    "Aleatoric is auto-disabled."
                )
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Epistemic Uncertainty (Fig. 3)")
            st.caption("Model uncertainty due to limited training data")
            
            # Auto-disable epistemic if sweeping label_noise
            if sweep_enabled and sweep_kind == "label_noise":
                epistemic_enabled = False
                st.caption("Epistemic controls hidden — not used for label-noise sweeps.")
            else:
                epistemic_enabled = st.checkbox(
                    "Enable epistemic uncertainty (under-trained classes)",
                    value=workflow["uncertainty_config"].get("epistemic_enabled", False),
                    help="Fig. 3 style — limits training data on selected classes.",
                )

            if epistemic_enabled:
                under_supported_mode = st.radio(
                    "Under-supported classes",
                    ["Random selection", "Manual selection"],
                    help="Classes with limited training data"
                )
                
                if under_supported_mode == "Random selection":
                    num_under = st.slider("Number of under-supported classes", 1, 5, 2)
                    under_supported = f"random:{num_under}"
                else:
                    class_names = ["airplane", "automobile", "bird", "cat", "deer", 
                                 "dog", "frog", "horse", "ship", "truck"]
                    selected_classes = st.multiselect(
                        "Select under-supported classes",
                        class_names,
                        default=class_names[:2]
                    )
                    under_supported = ",".join([str(class_names.index(c)) for c in selected_classes])
                
                under_train_per_class = st.number_input(
                    "Samples per under-supported class",
                    min_value=10, max_value=500, value=50, step=10
                )
                regular_train_per_class = st.number_input(
                    "Samples per regular class",
                    min_value=50, max_value=1000, value=300, step=50
                )
            else:
                under_supported = None
                under_train_per_class = None
                regular_train_per_class = 300

        # Aleatoric Uncertainty (Label Noise)
        with col2:
            st.markdown("#### Aleatoric Uncertainty (Fig. 4)")
            st.caption("Data uncertainty due to label noise")
            
            noise_type = workflow['dataset_config'].get('noise_type', 'clean_label')
            dataset_name = workflow['dataset_config'].get('dataset_name', 'cifar10')
            uses_cifar10n_noise = (
                dataset_name == "cifar10n" and not _is_clean_noise(noise_type)
            )

            if sweep_enabled and sweep_kind == "label_noise":
                st.caption(
                    f"✓ Aleatoric axis: sweep grid `{LABEL_NOISE_SWEEP[sweep_mode]}` — "
                    "no extra checkbox needed."
                )
                aleatoric_enabled = True
                custom_noise = None
            elif sweep_enabled and sweep_kind == "dataset_size":
                aleatoric_enabled = False
                custom_noise = None
                st.caption("Aleatoric controls hidden — not used for dataset-size sweeps.")
            elif uses_cifar10n_noise:
                aleatoric_enabled = st.checkbox(
                    f"Use CIFAR-10N noise ({CIFAR10N_NOISE_LABELS.get(noise_type, noise_type)})",
                    value=True,
                    help="Train with human-annotated noisy labels from the selected CIFAR-10N split.",
                )
                custom_noise = None
            elif not _is_clean_noise(noise_type):
                aleatoric_enabled = st.checkbox(
                    f"Use dataset noise ({noise_type})",
                    value=True,
                    help=f"Use CIFAR-10N {noise_type} noise labels",
                )
                custom_noise = None
            else:
                aleatoric_enabled = st.checkbox("Add custom label noise", value=False)
                if aleatoric_enabled:
                    custom_noise = st.slider(
                        "Custom noise rate (%)",
                        0, 50, 10, 5,
                    ) / 100.0
                else:
                    custom_noise = None
        
        # Dataset preview
        if epistemic_enabled:
            st.markdown("#### Dataset Configuration Preview")
            if under_supported and under_train_per_class and regular_train_per_class:
                if under_supported.startswith("random:"):
                    num_under = int(under_supported.split(":")[1])
                else:
                    num_under = len(under_supported.split(","))
                
                num_regular = 10 - num_under
                under_samples = num_under * under_train_per_class
                regular_samples = num_regular * regular_train_per_class
                total_samples = under_samples + regular_samples
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Under-supported", f"{under_samples:,} samples")
                with col2:
                    st.metric("Regular classes", f"{regular_samples:,} samples")
                with col3:
                    st.metric("Total training", f"{total_samples:,} samples")
        
        # Continue button
        if st.button("✓ Continue to Evaluation Setup", type="primary", use_container_width=True):
            workflow['step3_complete'] = True
            workflow['uncertainty_config'] = {
                'epistemic_enabled': (
                    False if (sweep_enabled and sweep_kind == "label_noise") else epistemic_enabled
                ),
                'under_supported': under_supported if epistemic_enabled else None,
                'under_train_per_class': under_train_per_class if epistemic_enabled else None,
                'regular_train_per_class': (
                    regular_train_per_class if epistemic_enabled else (regular_train_per_class or 300)
                ),
                'aleatoric_enabled': (
                    True if (sweep_enabled and sweep_kind == "label_noise") else aleatoric_enabled
                ),
                'custom_noise_rate': custom_noise if aleatoric_enabled else None,
                'sweep_enabled': sweep_enabled,
                'sweep_kind': sweep_kind,
                'sweep_mode': sweep_mode,
                'epistemic_sweep_enabled': sweep_enabled and sweep_kind == "dataset_size",
                'epistemic_sweep_values': aligned_under_train_sweep(sweep_mode),
                'aleatoric_sweep_enabled': sweep_enabled and sweep_kind == "label_noise",
                'aleatoric_sweep_values': LABEL_NOISE_SWEEP[sweep_mode],
            }
            if sweep_enabled:
                tc = TRAINING_CONFIG[sweep_mode]
                workflow["training_config"]["epochs"] = tc["epochs"]
                if "evaluation_config" not in workflow:
                    workflow["evaluation_config"] = {}
                workflow["evaluation_config"]["mc_passes"] = tc["mc_passes"]
                if sweep_kind == "label_noise":
                    workflow["dataset_config"]["noise_type"] = "clean_label"
                    workflow["uncertainty_config"]["custom_noise_rate"] = None
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 4: EVALUATION SETUP ==========
    if not ui_on("step4_evaluation"):
        pass
    elif workflow['step4_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            eval_per_group = workflow['evaluation_config']['eval_per_group']
            mc_passes = workflow['evaluation_config']['mc_passes']
            st.markdown(f"**✅ Step 4: Evaluation** - {eval_per_group} samples/group, {mc_passes} MC passes")
        with col2:
            if st.button("Edit", key="edit_step4"):
                workflow['step4_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 4: Evaluation Setup")
        
        st.markdown("#### Evaluation Pool Configuration")
        
        # Calculate available samples
        dataset_stats = workflow['dataset_config'].get('stats', {})
        total_samples = dataset_stats.get('total_samples', 50000)
        
        # Estimate training samples used
        if workflow['uncertainty_config'].get('epistemic_enabled'):
            under_train = workflow['uncertainty_config'].get('under_train_per_class', 50)
            regular_train = workflow['uncertainty_config'].get('regular_train_per_class', 300)
            under_supported = workflow['uncertainty_config'].get('under_supported', 'random:2')
            
            if under_supported.startswith("random:"):
                num_under = int(under_supported.split(":")[1])
            else:
                num_under = len(under_supported.split(","))
            
            num_regular = 10 - num_under
            estimated_train = (num_under * under_train) + (num_regular * regular_train)
        else:
            estimated_train = 2500  # Default estimate
        
        available_for_eval = total_samples - estimated_train
        
        st.info(f"📊 Estimated available for evaluation: ~{available_for_eval:,} samples")
        
        # Evaluation configuration
        col1, col2 = st.columns(2)
        
        with col1:
            eval_per_group = st.number_input(
                "Samples per evaluation group",
                min_value=50,
                max_value=500,
                value=100,
                step=50,
                help="Number of samples to evaluate per group (under-supported, regular-clean, regular-noisy)"
            )
            
            # Calculate total evaluation samples
            num_groups = 3 if workflow['uncertainty_config'].get('epistemic_enabled') else 2
            total_eval = eval_per_group * num_groups
            st.caption(f"Total evaluation samples: {total_eval:,}")
        
        with col2:
            mc_passes = st.number_input(
                "MC Dropout passes",
                min_value=1,
                max_value=50,
                value=20,
                help="Number of forward passes with dropout for uncertainty estimation"
            )
        
        # Uncertainty signals selection
        st.markdown("#### Uncertainty Signals")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Epistemic Signals**")
            epistemic_signals = []
            if st.checkbox("inverse_mass", value=True):
                epistemic_signals.append("inverse_mass")
            if st.checkbox("dominance", value=True):
                epistemic_signals.append("dominance")
            if st.checkbox("inverse_logit_magnitude", value=True):
                epistemic_signals.append("inverse_logit_magnitude")
        
        with col2:
            st.markdown("**Aleatoric Signals**")
            aleatoric_signals = []
            if st.checkbox("inverse_coherence", value=True):
                aleatoric_signals.append("inverse_coherence")
        
        with col3:
            st.markdown("**Baseline Signals**")
            baseline_signals = []
            if st.checkbox("msp_uncertainty", value=True):
                baseline_signals.append("msp_uncertainty")
            if st.checkbox("predictive_entropy", value=True):
                baseline_signals.append("predictive_entropy")
            if st.checkbox("mutual_info", value=True):
                baseline_signals.append("mutual_info")
        
        all_signals = epistemic_signals + aleatoric_signals + baseline_signals
        
        if not all_signals:
            st.warning("⚠️ Please select at least one uncertainty signal")
            st.stop()
        
        # Continue to review
        if st.button("✓ Review & Launch Experiment", type="primary", use_container_width=True):
            workflow['step4_complete'] = True
            workflow['evaluation_config'] = {
                'eval_per_group': eval_per_group,
                'mc_passes': mc_passes,
                'selected_signals': all_signals
            }
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    # ========== STEP 5: REVIEW ==========
    if ui_on("step5_launch"):
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🚀 Step 5: Review")

        sweep_type, sweep_configs = _generate_sweep_configs(workflow)
        n_runs = len(sweep_configs)

        uc = workflow.get("uncertainty_config", {})
        if (
            uc.get("sweep_enabled")
            and uc.get("sweep_kind") == "label_noise"
            and uc.get("epistemic_enabled")
        ):
            st.warning(
                "**Mixed uncertainty:** label-noise sweep with epistemic under-training enabled. "
                "Consider disabling epistemic uncertainty in Step 3 for cleaner Fig. 4 results."
            )

        if n_runs > 1:
            st.success(
                f"**Fast sweep ready:** {n_runs} experiments on `{sweep_type.value}` "
                f"(mode `{_sweep_mode(workflow)}`) — same grid as Hypothesis Validation quick."
            )
        else:
            st.warning(
                "Sweep is **off** in Step 3 — only one run would be created. "
                "Use **Paper sweeps** in the sidebar for Fig. 3 + Fig. 4 campaigns."
            )

        mode = _sweep_mode(workflow)
        summary = aligned_sweep_summary(mode)
        with st.expander("Sweep grid preview", expanded=False):
            st.caption(f"Mode: **{mode}**")
            st.caption(f"Fig. 3 (under-train): `{summary['under_train_per_class']}`")
            st.caption(f"Fig. 4 (label noise %): `{summary['label_noise_percent']}`")

        st.markdown('</div>', unsafe_allow_html=True)

    # Results section at bottom — only when explicitly enabled in UI debug
    if ui_on("results_section"):
        st.markdown("---")
        st.markdown("### � Experiment Results & Progress")
        st.caption(
            f"Live data from `{API_BASE_URL}`. "
            "Enable sub-toggles in UI debug to show sweeps, tables, etc."
        )
        _render_progressive_results_section()

    render_experiment_stats_footer(API_BASE_URL, get_headers)

    if ui_on("footer"):
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: gray;'>
            <small>Uncertainty Quantification Experiment Builder | Progressive Disclosure UI</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

# Made with Bob
