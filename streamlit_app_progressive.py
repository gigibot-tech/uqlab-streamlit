"""
Progressive Disclosure Streamlit App for Uncertainty Quantification.

Thin shell: workflow steps + orchestrator launch + results panel.
See START_HERE.md for architecture.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC = _PROJECT_ROOT / "src"
for _path in (_SRC, _PROJECT_ROOT):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import requests
import streamlit as st

from uqlab.data.dataset_registry import get_dataset_spec
from uqlab_orchestrator import (
    generate_sweep_configs,
    launch_paired_paper_profiles,
    launch_paper_profile,
    launch_workflow_experiments,
)
from uqlab_orchestrator.config import (
    CIFAR10N_NOISE_LABELS,
    DATASET_CATALOG,
    fallback_dataset_stats,
)
from uqlab.ui_components.progressive import (
    render_launch_result,
    render_progressive_results_section,
)
from uqlab.ui_components.progressive.sweep_launch_cards import SweepLaunchCallbacks
from uqlab.ui_components.progressive.api_client import fetch_experiments
from uqlab.ui_components.results.experiment_results_panel import render_experiment_stats_footer
from uqlab.ui_components.selectors.paper_sweep_launch import render_sidebar_paper_launch
from uqlab.ui_components.selectors.sidebar_controls import render_sidebar_footer_debug
from uqlab.ui_components.selectors.smart_experiment_selector import render_sidebar_experiment_selector
from uqlab.ui_components.ui_debug import ui_on
from uqlab.ui_components.workflow import (
    ensure_workflow_initialized,
    render_step2_training,
    render_step3_collapsed,
    render_step3_uncertainty,
    render_step4_evaluation,
    render_step5_review,
)
from uqlab.ui_components.workflow.step1_dataset import render_step1_dataset

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")


def _set_highlight_experiment(exp_id: str) -> None:
    st.session_state.highlight_experiment_id = exp_id


def get_headers() -> dict:
    headers: dict = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


def fetch_dataset_stats(
    dataset_name: str,
    noise_type: str,
    *,
    quiet: bool = False,
) -> dict:
    try:
        url = f"{API_BASE_URL}/api/v1/datasets/{dataset_name}/stats"
        response = requests.get(
            url,
            params={"noise_type": noise_type},
            headers=get_headers(),
            timeout=10,
        )
        if response.status_code == 400:
            raise requests.exceptions.HTTPError("unsupported dataset on backend")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        try:
            from uqlab_orchestrator.config import compute_dataset_stats

            return compute_dataset_stats(dataset_name, noise_type, download=False)
        except Exception:
            if not quiet:
                st.warning("Backend unavailable — using offline dataset stats.")
            return fallback_dataset_stats(dataset_name, noise_type)


st.set_page_config(
    page_title="UQ Experiment Builder",
    page_icon="🔬",
    layout="wide",
)

st.markdown(
    """
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
</style>
""",
    unsafe_allow_html=True,
)


def _make_launch_callbacks(workflow: Dict[str, Any]) -> SweepLaunchCallbacks:
    return SweepLaunchCallbacks(
        on_launch_custom=lambda auto: launch_workflow_experiments(
            workflow,
            auto_start=auto,
            highlight_callback=_set_highlight_experiment,
        ),
        on_launch_fig3=lambda auto: launch_paper_profile(
            workflow,
            "under_train",
            auto_start=auto,
            highlight_callback=_set_highlight_experiment,
        ),
        on_launch_fig4=lambda auto: launch_paper_profile(
            workflow,
            "noise",
            auto_start=auto,
            highlight_callback=_set_highlight_experiment,
        ),
        on_launch_both=lambda auto: launch_paired_paper_profiles(
            workflow,
            auto_start=auto,
            highlight_callback=_set_highlight_experiment,
        ),
    )


def main() -> None:
    if ui_on("page_title"):
        st.title("🔬 Uncertainty Quantification Experiment Builder")
        st.caption(
            "Configure Steps 1–4, **launch in Step 5** (or sidebar quick launch), "
            "then scroll to **Results** below. See **START_HERE.md**."
        )

    ensure_workflow_initialized()
    workflow = st.session_state.workflow
    launch_callbacks = _make_launch_callbacks(workflow)

    with st.sidebar:
        render_sidebar_paper_launch(
            workflow,
            on_launch_custom=launch_callbacks.on_launch_custom,
            on_launch_both=launch_callbacks.on_launch_both,
            on_launch_epis=launch_callbacks.on_launch_fig3,
            on_launch_alea=launch_callbacks.on_launch_fig4,
        )
        if st.session_state.get("experiment_selection_in_sidebar", True):
            try:
                sidebar_experiments = fetch_experiments(API_BASE_URL, get_headers)
                render_sidebar_experiment_selector(
                    sidebar_experiments,
                    workflow,
                    key_prefix="sb",
                )
            except Exception as exc:
                st.caption(f"Could not load experiments: {exc}")
        render_sidebar_footer_debug()

    render_launch_result()

    if not ui_on("step1_dataset"):
        pass
    elif workflow["step1_complete"]:
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            dataset_name = workflow["dataset_config"]["dataset_name"]
            noise_type = workflow["dataset_config"].get("noise_type", "clean_label")
            ds_label = DATASET_CATALOG.get(dataset_name, {}).get("short", dataset_name.upper())
            try:
                spec = get_dataset_spec(dataset_name)
            except ValueError:
                spec = None
            if spec and spec.supports_human_noise:
                noise_label = CIFAR10N_NOISE_LABELS.get(noise_type, noise_type)
                st.markdown(f"**✅ Step 1: Dataset** — {ds_label} · {noise_label}")
            else:
                st.markdown(f"**✅ Step 1: Dataset** — {ds_label} (clean labels)")
        with col2:
            if st.button("Edit", key="edit_step1"):
                workflow["step1_complete"] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step1_dataset(workflow, fetch_stats=fetch_dataset_stats)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if not ui_on("step2_training"):
        pass
    elif workflow["step2_complete"]:
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            tc = workflow["training_config"]
            if tc.get("use_checkpoint"):
                checkpoint_id = tc.get("checkpoint_id", "?")
                extra = tc.get("additional_epochs")
                prior = tc.get("prior_epochs")
                if prior is not None and extra is not None:
                    st.markdown(
                        f"**✅ Step 2: Training** — resume `{checkpoint_id[:8]}…` "
                        f"({prior} + {extra} = {tc.get('epochs')} epochs)"
                    )
                else:
                    st.markdown(f"**✅ Step 2: Training** - Using checkpoint: {checkpoint_id}")
            else:
                model_arch = workflow["training_config"]["model_architecture"]
                epochs = workflow["training_config"]["epochs"]
                lr = workflow["training_config"].get("learning_rate", 0.001)
                st.markdown(f"**✅ Step 2: Training** — {model_arch}, {epochs} epochs, lr={lr}")
        with col2:
            if st.button("Edit", key="edit_step2"):
                workflow["step2_complete"] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 🧠 Step 2: Training Setup")
        render_step2_training(
            workflow,
            api_base_url=API_BASE_URL,
            get_headers=get_headers,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if not ui_on("step3_uncertainty"):
        pass
    elif workflow["step3_complete"]:
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            render_step3_collapsed(workflow)
        with col2:
            if st.button("Edit", key="edit_step3"):
                workflow["step3_complete"] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step3_uncertainty(workflow)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if not ui_on("step4_evaluation"):
        pass
    elif workflow["step4_complete"]:
        st.markdown('<div class="step-complete">', unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            eval_per_group = workflow["evaluation_config"]["eval_per_group"]
            mc_passes = workflow["evaluation_config"]["mc_passes"]
            st.markdown(
                f"**✅ Step 4: Evaluation** - {eval_per_group} samples/group, "
                f"{mc_passes} MC passes"
            )
        with col2:
            if st.button("Edit", key="edit_step4"):
                workflow["step4_complete"] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        st.markdown("### 📊 Step 4: Evaluation Setup")
        render_step4_evaluation(workflow)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if ui_on("step5_launch"):
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step5_review(
            workflow,
            api_base_url=API_BASE_URL,
            get_headers=get_headers,
            project_root=_PROJECT_ROOT,
            generate_sweep_configs=generate_sweep_configs,
            launch_callbacks=launch_callbacks,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div id="results-section"></div>', unsafe_allow_html=True)
    render_progressive_results_section(API_BASE_URL, get_headers)

    render_experiment_stats_footer(API_BASE_URL, get_headers)

    if ui_on("footer"):
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "<small>Uncertainty Quantification Experiment Builder | Progressive Disclosure UI</small>"
            "</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
