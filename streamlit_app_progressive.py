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
# Note: The following modules are not yet implemented:
# - uqlab.ui_components.results (partial implementation only)
# - uqlab.ui_components.selectors.smart_experiment_selector (not created)
# - uqlab.ui_components.visualization.signals.signal_sweep_paper_viz (not created)
#
# from uqlab.ui_components.results import render_experiment_results
# from uqlab.ui_components.selectors.smart_experiment_selector import (
#     render_smart_experiment_selector,
#     render_sweep_launch_controls,
#     render_sweep_launch_toolbar,
# )
# from uqlab.ui_components.visualization.signals.signal_sweep_paper_viz import (
#     render_production_signal_sweep_grid,
# )


# ============================================================================
# STUB FUNCTIONS FOR MISSING MODULES
# These functions are placeholders for modules that haven't been implemented yet
# ============================================================================

def fetch_experiments_for_ui(api_base_url: str, get_headers_func) -> List[Dict]:
    """Stub function - not yet implemented"""
    return []

def render_experiment_results_panel(api_base_url: str, get_headers_func, auto_refresh: bool, **kwargs) -> bool:
    """Stub function - not yet implemented
    
    Accepts all parameters but ignores them:
    - caption, empty_message, highlight_experiment_id, key_prefix
    - detail_mode, show_batch_visualizations, show_signal_sweep_plots
    - workflow, show_experiment_selection, show_launch_controls
    """
    st.warning("⚠️ Experiment results panel not yet implemented")
    return auto_refresh

def render_sweep_launch_toolbar(*args, **kwargs):
    """Stub function - not yet implemented"""
    st.warning("⚠️ Sweep launch toolbar not yet implemented")

def render_sweep_launch_controls(*args, **kwargs):
    """Stub function - not yet implemented"""
    st.warning("⚠️ Sweep launch controls not yet implemented")

def render_local_validation_viz(*args, **kwargs):
    """Stub function - not yet implemented"""
    st.warning("⚠️ Local validation visualization not yet implemented")

def render_preset_validation_sweeps(*args, **kwargs):
    """Stub function - not yet implemented"""
    st.warning("⚠️ Preset validation sweeps not yet implemented")

# ============================================================================
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
        "model_architecture": "dinov2-small",
        "hidden_dim": 256,
        "dropout": 0.2,
        "epochs": TRAINING_CONFIG["quick"]["epochs"],
        "learning_rate": 0.001,
        "batch_size": 256,
    },
    "uncertainty_config": {
        "epistemic_enabled": True,
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


def _is_clean_noise(noise_type: str) -> bool:
    return noise_type in ("none", "clean_label", "clean", "no_noise")


def _fallback_dataset_stats(noise_type: str) -> dict:
    """Offline stats when the FastAPI backend is not running."""
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
    
    # Override values if provided
    under = under_train_per_class if under_train_per_class is not None else uncertainty.get("under_train_per_class", 50)
    
    # Calculate aleatoric noise percentage with proper validation
    if aleatoric_noise_percentage is not None:
        # Explicit override (used in sweeps)
        alea_pct = float(aleatoric_noise_percentage)
    else:
        # Determine from workflow config
        aleatoric_enabled = uncertainty.get("aleatoric_enabled", False)
        custom_noise = uncertainty.get("custom_noise_rate")
        noise_type = dataset.get("noise_type", "clean_label")
        
        if not aleatoric_enabled:
            # Aleatoric disabled = no noise
            alea_pct = 0.0
        elif custom_noise is not None:
            # Custom noise specified
            alea_pct = float(custom_noise) * 100.0
        elif not _is_clean_noise(noise_type):
            # Using dataset noise (CIFAR-10N)
            stats = dataset.get("stats", {})
            dataset_noise_rate = stats.get("noise_rate", 0.0)
            alea_pct = float(dataset_noise_rate) * 100.0
        else:
            # Clean dataset, no custom noise = no noise
            alea_pct = 0.0
    
    # Determine architecture from model selection
    model_arch = training.get("model_architecture", "dinov2-small")
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
            noise_type=dataset.get("noise_type", "worse_label"),
            under_supported_classes=uncertainty.get("under_supported", "random:2"),
            under_train_per_class=int(under),
            regular_train_per_class=uncertainty.get("regular_train_per_class", 300),
            aleatoric_noise_percentage=alea_pct,
            eval_per_group=evaluation["eval_per_group"],
        ),
        model=ModelConfig(
            architecture=architecture,
            dinov2_model=dinov2_model,
            hidden_dim=training.get("hidden_dim", 256),
            dropout=training.get("dropout", 0.2),
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
) -> Dict[str, Any]:
    """Generate configs using BatchGenerator and submit to API."""
    sweep_type, configs = _generate_sweep_configs(workflow)
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
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
    }


def _render_progressive_results_section() -> None:
    """API results table + unified experiment visualization (smart selector)."""
    # Note: These functions don't exist in validation_runner, using stubs instead
    # from uqlab.ui_components.orchestration.validation_runner import (
    #     render_local_validation_viz,
    #     render_preset_validation_sweeps,
    # )

    with st.expander("Launch local preset sweeps (Fig. 3 / Fig. 4)", expanded=False):
        render_preset_validation_sweeps(key_prefix="prog_preset", show_viz=False)
    render_local_validation_viz(key_prefix="prog_preset_viz")
    st.markdown("---")
    st.markdown("### 📊 All API experiments (table)")
    st.session_state.results_auto_refresh = render_experiment_results_panel(
        API_BASE_URL,
        get_headers,
        st.session_state.results_auto_refresh,
        caption=(
            f"Live data from `{API_BASE_URL}`. "
            "Enable auto-refresh while a run is **running**."
        ),
        empty_message=(
            "No experiments in the database yet. Use **Launch Experiment** in Step 5 below."
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
        return _fallback_dataset_stats(noise_type)


def main():
    st.title("🔬 Uncertainty Quantification Experiment Builder")
    st.caption(
        "Configure Steps 1–4, then **Step 5** to launch sweeps and view results. "
        "Pick a campaign in the **sidebar**."
    )

    _ensure_workflow_initialized()
    workflow = st.session_state.workflow

    # Sidebar - Progress Tracker
    with st.sidebar:
        st.markdown("### ⚙️ Configuration Progress")
        st.markdown("---")

        steps = [
            ("📊", "Dataset Selection", workflow["step1_complete"]),
            ("🧠", "Training Setup", workflow["step2_complete"]),
            ("🎲", "Uncertainty Config", workflow["step3_complete"]),
            ("📊", "Evaluation Setup", workflow["step4_complete"]),
        ]

        for icon, name, complete in steps:
            if complete:
                st.markdown(f"✅ {icon} **{name}**")
            else:
                st.markdown(f"⬜ {icon} {name}")

        experiments = fetch_experiments_for_ui(API_BASE_URL, get_headers)
        if experiments:
            from uqlab.ui_components.selectors.smart_experiment_selector import render_sidebar_experiment_selector

            disk_only = sum(1 for e in experiments if e.get("_source") == "disk")
            if disk_only and disk_only == len(experiments):
                from uqlab.runtime_paths import sqlite_db_path

                st.caption(
                    f"On-disk only ({disk_only} run(s)) — API DB empty · `{sqlite_db_path()}`"
                )
            render_sidebar_experiment_selector(
                experiments,
                workflow,
                key_prefix="sb",
            )
        elif experiments is None:
            st.markdown("---")
            st.caption("⚠️ API offline — experiment list unavailable")
        else:
            from uqlab.runtime_paths import sqlite_db_path

            st.markdown("---")
            st.caption(
                f"API online · **0** experiments in DB (`{sqlite_db_path()}`). "
                "Use **Step 5 Launch** or **Run both** (API), or **local preset sweeps** "
                "(`results/validation/`, not this list)."
            )

        st.markdown("---")

        if st.button("↺ Reset to recommended defaults", use_container_width=True):
            st.session_state.workflow = _default_workflow()
            st.session_state.launch_result = None
            st.rerun()

        if st.button("🔄 Start from scratch", help="Clear all steps", use_container_width=True):
            st.session_state.workflow = _empty_workflow()
            st.session_state.launch_result = None
            st.rerun()
    
    # ========== STEP 1: DATASET SELECTION ==========
    if workflow['step1_complete']:
        # Show collapsed summary
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            dataset_name = workflow['dataset_config']['dataset_name']
            noise_type = workflow['dataset_config'].get('noise_type', 'none')
            st.markdown(f"**✅ Step 1: Dataset** - {dataset_name.upper()} ({noise_type})")
        with col2:
            if st.button("Edit", key="edit_step1"):
                workflow['step1_complete'] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Show active step
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 1: Dataset Selection")
        
        # Dataset selection
        dataset_choice = selectbox_without_default(
            "Choose a dataset",
            ["cifar10"],
            help_text="CIFAR-10: 50,000 training images, 10 classes"
        )
        
        if not dataset_choice:
            st.info("👆 Please select a dataset to continue")
            st.stop()
        
        # Noise type selection
        noise_options = list(CIFAR10N_NOISE_OPTIONS)
        saved_noise = workflow["dataset_config"].get("noise_type", "worse_label")
        if saved_noise == "none":
            saved_noise = "clean_label"
        default_noise_idx = (
            noise_options.index(saved_noise)
            if saved_noise in noise_options
            else noise_options.index("worse_label")
        )
        noise_choice = st.selectbox(
            "Label noise type",
            noise_options,
            index=default_noise_idx,
            help="CIFAR-10N provides synthetic noisy labels for uncertainty research",
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
    if workflow['step2_complete']:
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
                model_arch = st.selectbox(
                    "Model architecture",
                    ["dinov2-small", "dinov2-base", "resnet18", "resnet50"],
                    help="DINOv2 models are pre-trained vision transformers"
                )
                hidden_dim = st.number_input("Hidden dimension", min_value=64, max_value=1024, value=256, step=64)
                dropout = st.slider("Dropout rate", 0.0, 0.5, 0.2, 0.05)
            
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
    if workflow['step3_complete']:
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
            help="Label noise → Fig. 4 style. Dataset size → Fig. 3 style.",
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
            else:
                vals = aligned_under_train_sweep(sweep_mode)
                st.caption(f"Will run **{len(vals)}** under-train sizes: {vals}")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        # Epistemic Uncertainty (Dataset Size)
        with col1:
            st.markdown("#### Epistemic Uncertainty")
            st.caption("Model uncertainty due to limited training data")
            
            epistemic_enabled = st.checkbox("Enable dataset size sweep", value=True)
            
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
                regular_train_per_class = None
        
        # Aleatoric Uncertainty (Label Noise)
        with col2:
            st.markdown("#### Aleatoric Uncertainty")
            st.caption("Data uncertainty due to label noise")
            
            noise_type = workflow['dataset_config'].get('noise_type', 'none')
            
            if not _is_clean_noise(noise_type):
                aleatoric_enabled = st.checkbox(
                    f"Use dataset noise ({noise_type})",
                    value=True,
                    help=f"Use CIFAR-10N {noise_type} noise labels"
                )
                custom_noise = None
            else:
                aleatoric_enabled = st.checkbox("Add custom label noise", value=False)
                if aleatoric_enabled:
                    custom_noise = st.slider(
                        "Custom noise rate (%)",
                        0, 50, 10, 5
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
                'epistemic_enabled': epistemic_enabled,
                'under_supported': under_supported if epistemic_enabled else None,
                'under_train_per_class': under_train_per_class if epistemic_enabled else None,
                'regular_train_per_class': regular_train_per_class if epistemic_enabled else None,
                'aleatoric_enabled': aleatoric_enabled,
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
    if workflow['step4_complete']:
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
            if st.checkbox("mutual_info", value=False):
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
    
    # ========== STEP 5: REVIEW & LAUNCH ==========
    st.markdown('<div class="step-active">', unsafe_allow_html=True)
    st.markdown("### 🚀 Step 5: Review & Launch")
    
    sweep_type, sweep_configs = _generate_sweep_configs(workflow)
    n_runs = len(sweep_configs)

    if n_runs > 1:
        st.success(
            f"**Fast sweep ready:** {n_runs} experiments on `{sweep_type.value}` "
            f"(mode `{_sweep_mode(workflow)}`) — same grid as Hypothesis Validation quick."
        )
    else:
        st.warning(
            "Sweep is **off** — only one run will be created. "
            "Enable **Launch a parameter sweep** in Step 3 for paper-style curves."
        )

    # Configuration summary
    st.markdown("#### Configuration Summary")
    
    with st.expander("📊 Dataset Configuration", expanded=True):
        dataset_config = workflow['dataset_config']
        st.write(f"**Dataset:** {dataset_config['dataset_name'].upper()}")
        st.write(f"**Noise type:** {dataset_config.get('noise_type', 'none')}")
        stats = dataset_config.get("stats") or _fallback_dataset_stats(
            dataset_config.get("noise_type", "worse_label")
        )
        st.write(f"**Total samples:** {stats.get('total_samples', 0):,}")
    
    with st.expander("🧠 Training Configuration", expanded=True):
        training_config = workflow['training_config']
        if training_config.get('use_checkpoint'):
            st.write(f"**Mode:** Using checkpoint")
            st.write(f"**Checkpoint ID:** {training_config['checkpoint_id']}")
        else:
            st.write(f"**Mode:** Train new model")
            st.write(f"**Architecture:** {training_config['model_architecture']}")
            st.write(f"**Epochs:** {training_config['epochs']}")
            st.write(f"**Learning rate:** {training_config['learning_rate']}")
    
    with st.expander("🎲 Uncertainty Configuration", expanded=True):
        uncertainty_config = workflow['uncertainty_config']
        if uncertainty_config.get("sweep_enabled"):
            st.write(
                f"**Sweep:** {uncertainty_config.get('sweep_kind')} "
                f"({uncertainty_config.get('sweep_mode')}) → **{n_runs}** API runs"
            )
            if sweep_type == SweepType.ALEATORIC_1D:
                st.write(f"**Noise % values:** {uncertainty_config.get('aleatoric_sweep_values')}")
            elif sweep_type == SweepType.EPISTEMIC_1D:
                st.write(f"**Under-train values:** {uncertainty_config.get('epistemic_sweep_values')}")
        st.write(f"**Epistemic enabled:** {uncertainty_config['epistemic_enabled']}")
        if uncertainty_config['epistemic_enabled']:
            st.write(f"**Under-supported:** {uncertainty_config['under_supported']}")
            st.write(f"**Under-supported samples:** {uncertainty_config['under_train_per_class']}")
            st.write(f"**Regular samples:** {uncertainty_config['regular_train_per_class']}")
        st.write(f"**Aleatoric enabled:** {uncertainty_config['aleatoric_enabled']}")
    
    with st.expander("📊 Evaluation Configuration", expanded=True):
        evaluation_config = workflow['evaluation_config']
        st.write(f"**Samples per group:** {evaluation_config['eval_per_group']}")
        st.write(f"**MC dropout passes:** {evaluation_config['mc_passes']}")
        st.write(f"**Signals:** {', '.join(evaluation_config['selected_signals'])}")
    
    st.markdown("#### 🚀 Launch paper sweeps (Fig. 3 + Fig. 4)")
    st.caption(
        "Paired **5+5** API runs (under-train + label noise). "
        "Uses quick/full grid from Step 3 sweep mode."
    )
    render_sweep_launch_toolbar(
        workflow,
        API_BASE_URL,
        get_headers,
        key_prefix="step5_paper",
    )
    with st.expander("Paper sweep options (quick / full)", expanded=False):
        render_sweep_launch_controls(
            workflow,
            API_BASE_URL,
            get_headers,
            key_prefix="step5_paper_opts",
        )

    st.markdown("#### Launch from Step 3 sweep settings")
    auto_start = st.checkbox(
        "Start training immediately after create",
        value=True,
        help="Calls POST /experiments/no-auth/{id}/start so the backend runs the ML script.",
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    launch_label = (
        f"🚀 Launch fast sweep ({n_runs} runs)"
        if n_runs > 1
        else "🚀 Launch single experiment"
    )
    with col1:
        launch_button = st.button(launch_label, type="primary", use_container_width=True)
    with col2:
        if st.button("Clear status", use_container_width=True):
            st.session_state.launch_result = None
            st.rerun()
    with col3:
        if st.button("← Reset defaults", use_container_width=True):
            st.session_state.workflow = _default_workflow()
            st.session_state.launch_result = None
            st.rerun()

    if launch_button:
        with st.spinner(
            f"Creating {n_runs} experiment(s) and starting training..."
            if n_runs > 1
            else "Creating experiment and starting training..."
        ):
            try:
                st.session_state.launch_result = _launch_workflow_experiments(
                    workflow,
                    auto_start=auto_start,
                )
            except requests.exceptions.RequestException as e:
                detail = e.response.text if getattr(e, "response", None) is not None else ""
                st.session_state.launch_result = {
                    "ok": False,
                    "error": str(e),
                    "detail": detail,
                }
            except Exception as e:
                st.session_state.launch_result = {
                    "ok": False,
                    "error": str(e),
                    "detail": None,
                }

    _render_launch_result()

    st.markdown('</div>', unsafe_allow_html=True)

    if workflow.get("step4_complete"):
        st.markdown("---")
        _render_progressive_results_section()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <small>Uncertainty Quantification Experiment Builder | Progressive Disclosure UI</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

# Made with Bob
