# Attribution artifacts (`zwischen/`)

Full eval×train influence matrices and aggregated attribution scalars written during
`collect_uncertainty_signals`.

See also: [`evaluation-protocol.md`](evaluation-protocol.md), [`PAPER_FLOW.md`](PAPER_FLOW.md).

---

## Layout under `<run_dir>/zwischen/`

| File | Shape / content | When written |
|------|-----------------|--------------|
| `00_eval_setup.pt` | eval indices, group labels | orchestrator |
| `01_deterministic_forward.pt` | logits for DualXDA targets | eval phase |
| `02_attribution_signals.pt` | DualXDA aggregated scalars (coherence, mass, …) | eval phase |
| `02_influence_dualxda.pt` | `scores`: `[n_eval, n_train]` DualXDA attribution | eval phase |
| `02_influence_graddot.pt` | `scores`: `[n_eval, n_train]` GradDot scores | when GradDot enabled |
| `02_influence_ek_fak.pt` | `scores`: `[n_eval, n_train]` EK-FAC scores | when EK-FAC enabled |
| `02b_ek_fak_*.pt` | EK-FAC aggregated scalars | eval phase |
| `02c_graddot_*.pt` | GradDot aggregated scalars | eval phase |
| `03_logit_signals.pt` | inverse logit magnitude | eval phase |
| `04_mc_dropout.pt` | MC entropy / mutual information | eval phase |
| `05_signal_table.pt` | final per-sample columns | eval phase |

Raw matrices are also cached under `<run_dir>/cache/` (GradDot, EK-FAC) during computation;
`02_influence_*.pt` copies the final tensor into the run artifact tree for assignment inspection.

---

## Assignment mapping

| Assignment piece | UQLab entry point |
|----------------|-------------------|
| Four-region split (noisy / sparse / clean / OOD) | `data.partition_mode: four_region` + `class_regions` — [`four_region.yaml`](../../configs/experiment/four_region.yaml) |
| Fashion-MNIST + pixel MLP | [`four_region_fashion_mlp.yaml`](../../configs/experiment/four_region_fashion_mlp.yaml) |
| CIFAR-10 + ResNet-18 | [`four_region_cifar_resnet.yaml`](../../configs/experiment/four_region_cifar_resnet.yaml) |
| Notebook (two runs + plot loop) | [`notebooks/four_region_benchmark.ipynb`](../../notebooks/four_region_benchmark.ipynb) |
| CLI | `python scripts/runners/run_fast_uncertainty_classification.py --config configs/experiment/four_region_fashion_mlp.yaml` |
| Per-sample metrics + four-pool plots | `per_sample_signals.csv` + [`four_region_reporting.py`](../../src/uqlab/evaluation/reporting/four_region_reporting.py) |

GradDot + DualXDA (+ optional EK-FAC) are enabled via `evaluation.signals.attribution` and
`evaluation.attribution_backends: [dualxda, graddot]` (see YAML presets above).
