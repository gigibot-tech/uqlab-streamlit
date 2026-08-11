# Small File Relocation Candidate — `configs/`

**Branch**: `cursor/small-file-relocation-candidates-684b`  
**Date**: 2026-08-11  
**Scope**: Identify whether the root-level `configs/` folder is a small-file relocation candidate.

---

## Executive Summary

The `configs/` folder at the repository root is a strong small-file relocation candidate. **All 11 files inside it are below 115 LoC**, well under both the 200 LoC and 300 LoC thresholds. The folder contains only YAML experiment/test presets and a short README.

The natural relocation target is `src/uqlab_core/configs/`, which would keep experiment configurations alongside the core package that consumes them. This relocation has been executed in other feature branches, so the pattern is established, but it requires updating references across documentation, notebooks, scripts, and the runtime path helper.

**Verdict**: `configs/` *can* be moved, but only as part of a coordinated reference-update pass.

---

## Methodology

- **Thresholds**: `< 200 LoC` (strong candidate) and `< 300 LoC` (still small).
- **Line count**: non-empty lines for text files; YAML files are counted as-is.
- **Excluded**: non-source files such as `.DS_Store`.

## File inventory

| File | LoC | Role | Candidate |
|------|----:|------|-----------|
| `configs/experiment/fast_pilot.yaml` | 20 | Experiment preset | Move |
| `configs/test/test_dinov2_mlp.yaml` | 25 | Test config | Move |
| `configs/test/test_resnet18_mcdropout.yaml` | 25 | Test config | Move |
| `configs/test/test_cnn_mcdropout.yaml` | 26 | Test config | Move |
| `configs/README.md` | 26 | Folder README | Move |
| `configs/example_resnet18_mcdropout.yaml` | 40 | Example config | Move |
| `configs/example_cnn_mcdropout.yaml` | 44 | Example config | Move |
| `configs/experiment/default.yaml` | 46 | Experiment preset | Move |
| `configs/experiment/four_region.yaml` | 48 | Experiment preset | Move |
| `configs/experiment/four_region_cifar_resnet.yaml` | 64 | Experiment preset | Move |
| `configs/experiment/four_region_fashion_mlp.yaml` | 64 | Experiment preset | Move |

**Summary**: 11 files, max 64 LoC, all under 115 LoC. The folder qualifies as a small-file relocation candidate by both thresholds.

## References found in the codebase

A non-exhaustive list of references that would need updating after relocation:

- `README.md:28,182` — root tree listing and description of `configs/`.
- `START_HERE.md:50` — CLI example using `configs/experiment/four_region.yaml`.
- `EXECUTION_FLOW_AND_CONFIG_GUIDE.md:65` — default CLI config path.
- `src/uqlab_core/runtime_paths.py:27` — helper that points to the configs directory.
- `src/uqlab_core/runner/notebook_run.py:86,91` — notebook preset paths.
- `src/uqlab_core/shared/config/classification.py:528` — default config path string.
- `scripts/setup/validate_architectures.py:11` — test config path.
- `scripts/setup/generate_thesis_diagram.py:12` — example config path.
- `docs/features/disentanglement-benchmark.md:22` — CLI example.
- `docs/features/ATTRIBUTION_ARTIFACTS.md:35-39` — relative links to YAML files.
- `docs/setup/CONFIG_AND_IMPORTS_STATUS.md:10,97,140,181` — status docs referencing `configs/`.
- `docs/migration/HYDRA_GUIDE.md` and `docs/migration/MIGRATION_GUIDE.md` — setup guides.
- `docs/phases/PHASE7_1_ARCHITECTURE_SELECTOR.md:207-230` — architecture docs.
- `notebooks/cifar10_paper_flow.ipynb`, `notebooks/attribution_distribution_uncertainty.ipynb`, `notebooks/watsonx_deployment_experiment.ipynb`, `notebooks/resnet_baseline_experiment.ipynb` — hard-coded config paths in notebook cells.
- `docs/user-guides/README_PARENT.md:28,161` — tree listing and description.

## Proposed relocation plan

### Target

```
configs/ → src/uqlab_core/configs/
```

### Rationale

- `configs/` is consumed primarily by `src/uqlab_core/` runners, notebooks, and the CLI.
- Co-locating configs with the core package makes the package self-contained for distribution.
- The move aligns with prior relocations of `uqlab-flask/` and small root scripts.

### Steps

1. Move the directory tree:
   ```bash
   git mv configs/ src/uqlab_core/configs/
   ```
2. Update `src/uqlab_core/runtime_paths.py` so the canonical configs directory returns the new path.
3. Update all documentation, notebook, and script references from `configs/` to `src/uqlab_core/configs/` (or use the runtime path helper instead of hard-coding).
4. Update `pyproject.toml` / package discovery if necessary so YAML files are included as package data.
5. Verify with `grep -R "configs/"` and run the relevant CLI smoke tests.

## Risk assessment

- **Low risk**: The folder is small and its contents are configuration files, not code.
- **Medium risk**: Many hard-coded references exist in notebooks (`.ipynb` JSON), markdown docs, and legacy scripts. A missed reference will cause CLI/notebook failures.
- **Mitigation**: Use the runtime path helper (`src/uqlab_core/runtime_paths.py`) consistently rather than string literals after the move.

## Recommendation

Relocate `configs/` to `src/uqlab_core/configs/` the next time a dedicated cleanup pass is scheduled. On this branch, document the candidate and the required reference updates; perform the move only if the reference-update pass can be completed and tested in the same iteration.
