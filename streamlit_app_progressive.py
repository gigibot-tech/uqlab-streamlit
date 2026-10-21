"""
Progressive Disclosure Streamlit App for Uncertainty Quantification.

Classification wizard (Steps 1–5). Preference-pair summarization is a separate
app: ``streamlit_app_prefsum.py`` (PrefSum).
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

import streamlit as st

from uqlab.ui_components.ui_debug import ui_on

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")


def get_headers() -> dict:
    headers: dict = {}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    return headers


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


def _run_classification_builder() -> None:
    """Lazy-import the image-classification wizard (needs full orchestrator)."""
    import requests

    from uqlab.data.datasets.registry import get_dataset_spec
    from uqlab_orchestrator import (
        launch_benchmark_both,
        launch_benchmark_primary,
    )
    from uqlab_orchestrator.config import (
        CIFAR10N_NOISE_LABELS,
        DATASET_CATALOG,
        fallback_dataset_stats,
    )
    from uqlab_orchestrator.launch_preflight import assess_launch_readiness
    from uqlab.ui_components.progressive.api_client import fetch_experiments
    from uqlab.ui_components.progressive.launch_results import render_launch_result
    from uqlab.ui_components.progressive.results_section import (
        render_progressive_results_section,
    )
    from uqlab.ui_components.progressive.sweep_launch_cards import SweepLaunchCallbacks
    from uqlab.ui_components.results.experiment_results_panel import (
        render_experiment_stats_footer,
    )
    from uqlab.ui_components.selectors.paper_sweep_launch import render_sidebar_paper_launch
    from uqlab.ui_components.selectors.sidebar_controls import render_sidebar_footer_debug
    from uqlab.ui_components.selectors.smart_experiment_selector import (
        render_sidebar_experiment_selector,
    )
    from uqlab.ui_components.workflow import (
        ensure_workflow_initialized,
        render_step2_training,
        render_step3_collapsed,
        render_step3_uncertainty,
        render_step4_evaluation,
        render_step5_review,
    )
    from uqlab.ui_components.workflow.step1_dataset import render_step1_dataset

    def _set_highlight_experiment(exp_id: str) -> None:
        st.session_state.highlight_experiment_id = exp_id

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

    def _make_launch_callbacks(workflow: Dict[str, Any]) -> SweepLaunchCallbacks:
        return SweepLaunchCallbacks(
            on_launch_primary=lambda auto: launch_benchmark_primary(
                workflow,
                auto_start=auto,
                highlight_callback=_set_highlight_experiment,
            ),
            on_launch_both=lambda auto, mirror_mode: launch_benchmark_both(
                workflow,
                auto_start=auto,
                mirror_mode=mirror_mode,  # type: ignore[arg-type]
                highlight_callback=_set_highlight_experiment,
            ),
        )

    def _apply_launch_workflow(workflow: Dict[str, Any], auto: bool) -> None:
        st.session_state.launch_result = launch_benchmark_primary(
            workflow,
            auto_start=auto,
            highlight_callback=_set_highlight_experiment,
        )
        st.session_state["scroll_to_results"] = True

    ensure_workflow_initialized()
    workflow = st.session_state.workflow
    launch_callbacks = _make_launch_callbacks(workflow)

    try:
        app_experiments = fetch_experiments(API_BASE_URL, get_headers)
    except Exception:
        app_experiments = []
    readiness = assess_launch_readiness(workflow, app_experiments, _PROJECT_ROOT)
    st.session_state.launch_readiness = readiness

    with st.sidebar:
        render_sidebar_paper_launch(
            workflow,
            readiness=readiness,
            on_launch_primary=launch_callbacks.on_launch_primary,
            on_launch_both=launch_callbacks.on_launch_both,
            on_apply_launch=_apply_launch_workflow,
        )
        if st.session_state.get("experiment_selection_in_sidebar", True):
            try:
                sidebar_experiments = app_experiments or fetch_experiments(
                    API_BASE_URL, get_headers
                )
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
            if spec and getattr(spec, "supports_human_noise", False):
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

    if ui_on("step2_5_checkpoint_arsenal"):
        from uqlab.ui_components.workflow.step2_5_checkpoint_arsenal import (
            render_step2_5_checkpoint_arsenal,
        )

        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step2_5_checkpoint_arsenal(
            app_experiments,
            workflow,
            key_prefix="step25",
        )
        st.markdown("</div>", unsafe_allow_html=True)

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
            render_step4_evaluation(workflow, collapsed=True)
        with col2:
            if st.button("Edit", key="edit_step4"):
                workflow["step4_complete"] = False
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step4_evaluation(workflow)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()

    if ui_on("step5_launch"):
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        render_step5_review(
            workflow,
            readiness=readiness,
            on_launch_primary=launch_callbacks.on_launch_primary,
            on_launch_both=launch_callbacks.on_launch_both,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if ui_on("results_section"):
        render_progressive_results_section(
            API_BASE_URL,
            get_headers,
            workflow=workflow,
        )
    render_experiment_stats_footer(API_BASE_URL, get_headers)


def main() -> None:
    if ui_on("page_title"):
        st.title("🔬 Uncertainty Quantification Experiment Builder")
        st.caption(
            "Classification Steps 1–5. For preference-pair summarization, run "
            "``streamlit run streamlit_app_prefsum.py`` (PrefSum)."
        )

    with st.sidebar:
        app_mode = st.radio(
            "App mode",
            ["Experiment builder", "Signal validation"],
            key="app_mode",
            horizontal=False,
        )

    if app_mode == "Signal validation" and ui_on("signal_validation"):
        try:
            from uqlab.ui_components.visualization.validation.signal_validation_tab import (
                render_signal_validation_tab,
            )
            from uqlab.ui_components.results.experiment_results_panel import (
                render_experiment_stats_footer,
            )

            render_signal_validation_tab()
            render_experiment_stats_footer(API_BASE_URL, get_headers)
        except Exception as exc:
            st.error(f"Signal validation unavailable: {exc}")
        return

    try:
        _run_classification_builder()
    except ModuleNotFoundError as exc:
        st.error(
            "Classification Experiment builder needs the full `uqlab_orchestrator` "
            f"package ({exc}). Preference pairs live in PrefSum: "
            "`streamlit run streamlit_app_prefsum.py`."
        )


if __name__ == "__main__":
    main()
