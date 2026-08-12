# Small-file relocation candidates

This report lists top-level folders whose files are all below the given LoC thresholds,
and assesses whether they can be relocated without breaking consumers.

Generated from: `/workspace`

## Summary

| Folder | Total files | < 200 LoC | 200-300 LoC | > 300 LoC |
|--------|-------------|-----------|-------------|-----------|
| `backend` | 108 | 91 | 7 | 10 |
| `configs` | 11 | 11 | 0 | 0 |
| `data` | 0 | - | - | - |
| `docs` | 347 | 231 | 48 | 68 |
| `notebooks` | 23 | 10 | 1 | 12 |
| `scripts` | 60 | 37 | 11 | 12 |
| `src` | 68 | 36 | 11 | 21 |
| `tests` | 63 | 52 | 4 | 7 |
| `uqlab-flask` | 18 | 15 | 2 | 1 |

*Thresholds considered: 200, 300 LoC.*

## Candidate details

### `configs/`

- **All files under 200 LoC:** 11/11
- **Location:** `configs`

| Lines | File |
|-------|------|
| 20 | `configs/experiment/fast_pilot.yaml` |
| 25 | `configs/test/test_dinov2_mlp.yaml` |
| 25 | `configs/test/test_resnet18_mcdropout.yaml` |
| 26 | `configs/README.md` |
| 26 | `configs/test/test_cnn_mcdropout.yaml` |
| 40 | `configs/example_resnet18_mcdropout.yaml` |
| 44 | `configs/example_cnn_mcdropout.yaml` |
| 46 | `configs/experiment/default.yaml` |
| 48 | `configs/experiment/four_region.yaml` |
| 64 | `configs/experiment/four_region_cifar_resnet.yaml` |
| 64 | `configs/experiment/four_region_fashion_mlp.yaml` |

**Consumers (references found):**

- `/workspace/EXECUTION_FLOW_AND_CONFIG_GUIDE.md`
  - `65: Default CLI config: [`configs/experiment/four_region.yaml`](configs/experiment/four_region.yaml) (`partition_mode: four_region`).`
- `/workspace/README.md`
  - `28: ├── configs/                      # Experiment configurations`
  - `182: - `configs/`: Experiment YAML configurations`
- `/workspace/START_HERE.md`
  - `50: --config configs/experiment/four_region.yaml \`
- `/workspace/docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`
  - `154: ├── configs/                    # YAML configs`
- `/workspace/docs/features/ATTRIBUTION_ARTIFACTS.md`
  - `35: | Four-region split (noisy / sparse / clean / OOD) | `data.partition_mode: four_region` + `class_regions` — [`four_region.yaml`](../../configs/experiment/four_region.yaml) |`
  - `36: | Fashion-MNIST + pixel MLP | [`four_region_fashion_mlp.yaml`](../../configs/experiment/four_region_fashion_mlp.yaml) |`
  - `37: | CIFAR-10 + ResNet-18 | [`four_region_cifar_resnet.yaml`](../../configs/experiment/four_region_cifar_resnet.yaml) |`
  - ... and 1 more
- `/workspace/docs/features/disentanglement-benchmark.md`
  - `22: --config configs/experiment/four_region.yaml \`
- `/workspace/docs/migration/HYDRA_GUIDE.md`
  - `34: @hydra.main(version_base=None, config_path="configs", config_name="experiment/default")`
  - `72: configs/`
  - `79: ### Default Config (`configs/experiment/default.yaml`)`
  - ... and 9 more
- `/workspace/docs/migration/MIGRATION_GUIDE.md`
  - `235: Create a test config in `configs/test/`:`
  - `238: # configs/test/test_my_custom_model.yaml`
  - `272: configs/test/test_my_custom_model.yaml \`
- `/workspace/docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md`
  - `207: 1. `configs/example_cnn_mcdropout.yaml` - CNN MC Dropout configuration`
  - `208: 2. `configs/example_resnet18_mcdropout.yaml` - ResNet18 MC Dropout configuration`
  - `229: - `uqlab-streamlit/configs/example_cnn_mcdropout.yaml`: Example CNN config`
  - ... and 1 more
- `/workspace/docs/setup/CONFIG_AND_IMPORTS_STATUS.md`
  - `10: Located in [`configs/`](configs:1):`
  - `12: configs/`
  - `97: ├── configs/                    # ✅ YAML configs (still used)`
  - ... and 2 more
- `/workspace/docs/user-guides/README_PARENT.md`
  - `28: ├── configs/                      # Configuration files`
  - `161: - `configs/`: Experiment configurations`
- `/workspace/notebooks/attribution_distribution_uncertainty.ipynb`
  - `97: "    cfg_path = PROJECT_ROOT / \"configs/experiment/four_region.yaml\"\n",`
- `/workspace/notebooks/cifar10_paper_flow.ipynb`
  - `57: "CONFIG_PATH = ROOT / \"configs/experiment/fast_pilot.yaml\"\n",`
  - `90: "Config: /Users/andrearachetta/Documents/old_pilots/uqlab-streamlit/configs/experiment/fast_pilot.yaml\n",`
  - `158: "    four_region_cfg_path = ROOT / \"configs/experiment/four_region_cifar_resnet.yaml\"\n",`
- `/workspace/notebooks/resnet_baseline_experiment.ipynb`
  - `805: "├── configs/                              # Experiment configurations\n",`
- `/workspace/notebooks/validation/RC9l Kopie.ipynb`
  - `105: "        'config_template': 'configs/test/test_dinov2_mlp.yaml',\n",`
  - `112: "        'config_template': 'configs/test/test_cnn_mcdropout.yaml',\n",`
  - `119: "        'config_template': 'configs/test/test_resnet18_mcdropout.yaml',\n",`
- `/workspace/notebooks/watsonx_deployment_experiment.ipynb`
  - `835: "├── configs/              # Experiment configurations\n",`
- `/workspace/scripts/setup/generate_thesis_diagram.py`
  - `12: --config configs/experiment/default.yaml \\`
- `/workspace/scripts/setup/validate_architectures.py`
  - `11: config_path = f"configs/test/{config_name}.yaml"`
- `/workspace/src/uqlab_core/runner/notebook_run.py`
  - `86: "config_path": root / "configs/experiment/four_region_fashion_mlp.yaml",`
  - `91: "config_path": root / "configs/experiment/four_region_cifar_resnet.yaml",`
- `/workspace/src/uqlab_core/runtime_paths.py`
  - `27: """Experiment YAML configs (``configs/experiment``, ``configs/test``, …)."""`
  - `28: return repository_root() / "configs"`
- `/workspace/src/uqlab_core/shared/config/classification.py`
  - `34: (matches ``configs/experiment/fast_pilot.yaml`` → ``default.yaml``).`
  - `528: default="configs/fast_uq_classification.yaml",`

**Movability assessment:**
- ⚠️  21 consumers reference this folder. Moving requires updating all of them.
- Suggested destination: `src/uqlab_core/configs/` as package data, or keep at root if YAML configs remain a user-facing entry point.
