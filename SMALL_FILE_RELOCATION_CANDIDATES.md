# Small File Relocation Candidates

**Generated**: 2026-09-05
**Branch**: `cursor/small-file-relocation-candidates-f223`
**Threshold**: files under 300 LoC (highlighted under 200 LoC where relevant)

## Summary

The following root-level folders contain files that are almost all under the 300 LoC threshold and are candidates for relocation, consolidation, or cleanup:

| Folder | Files Total | Files < 300 LoC | Notes |
|--------|-------------|-------------------|-------|
| `data/` | 1 | 1 (100%) | Contains only a `.gitkeep`; effectively unused. |
| `configs/` | 10 | 10 (100%) | All YAML files under 70 LoC; config sprawl at root. |
| `uqlab-flask/` | 14 | 13 (93%) | Small legacy Flask wizard; most files under 300 LoC. |
| `tests/` | 46 | 39 (85%) | Many small tests; root-level tests may fit better inside `src/`. |
| `docs/` | 100+ | 100+ | Mostly auto-generated component stubs; see consolidation note. |

Additionally, three broken symlinks were found that should be removed.

---

## 1. `data/` — Empty folder candidate

```
data/
└── .gitkeep          (0 LoC)
```

**Recommendation**: Remove the folder or replace the `.gitkeep` with documentation explaining where data is stored. If the project uses runtime data directories elsewhere, this folder is redundant.

---

## 2. `configs/` — Small config files at root

All files are under 70 LoC:

```
configs/
├── example_cnn_mcdropout.yaml              (40 LoC)
├── example_resnet18_mcdropout.yaml           (44 LoC)
├── test/
│   ├── test_cnn_mcdropout.yaml             (25 LoC)
│   ├── test_dinov2_mlp.yaml                (25 LoC)
│   └── test_resnet18_mcdropout.yaml        (26 LoC)
└── experiment/
    ├── default.yaml                          (45 LoC)
    ├── fast_pilot.yaml                       (19 LoC)
    ├── four_region.yaml                      (48 LoC)
    ├── four_region_cifar_resnet.yaml         (64 LoC)
    └── four_region_fashion_mlp.yaml          (64 LoC)
```

**Recommendation**: Move `configs/` under `src/` or the orchestrator package so configuration lives next to the code that consumes it. For example:

```
src/uqlab_orchestrator/configs/
├── examples/
└── experiments/
```

This keeps root-level directories focused on high-level project concerns (docs, tests, backend, notebooks) rather than config data.

---

## 3. `uqlab-flask/` — Small legacy Flask app

All files are small except `executor.py` (652 LoC):

```
uqlab-flask/
├── app.py                                     (37 LoC)
├── requirements.txt                           (2 LoC)
├── README.md                                  (33 LoC)
├── uqlab_flask/
│   ├── __init__.py                            (1 LoC)
│   ├── executor.py                            (652 LoC)  ← exceeds threshold
│   ├── routes/
│   │   ├── __init__.py                        (0 LoC)
│   │   ├── runs.py                            (139 LoC)
│   │   └── wizard.py                          (282 LoC)
│   ├── static/style.css                       (177 LoC)
│   └── templates/                             (all under 35 LoC)
```

**Recommendation**: This looks like a deprecated or experimental Flask wizard. Options:

1. **Archive** the whole folder under `scripts/deployment/legacy/` or `archive/`.
2. **Merge** into `backend/` if it provides useful API routes, after splitting `executor.py` into the existing execution facade pattern.
3. **Delete** if the Streamlit app (`streamlit_app_progressive.py`) has replaced it.

Before moving, verify whether `uqlab-flask` is still referenced in docs, CI, or deployment scripts.

---

## 4. `tests/` — Root-level tests with many small files

39 of 46 files are under 300 LoC; 25 are under 100 LoC. Examples:

```
tests/
├── __init__.py                              (11 LoC)
├── test_minimal.py                          (24 LoC)
├── test_dead_code_imports.py                (32 LoC)
├── test_aleatoric_split.py                  (38 LoC)
├── test_dataset_factory.py                  (42 LoC)
├── test_four_region_eval.py                 (42 LoC)
├── test_runner_pipeline.py                  (54 LoC)
├── test_ui_import_is_light.py               (64 LoC)
├── test_campaign_paper_score.py             (58 LoC)
├── test_parse_under_supported_classes.py    (19 LoC)
└── legacy/                                   (many small files)
```

**Recommendation**: Move tests next to the packages they exercise, e.g.:

```
src/uqlab_core/tests/
src/uqlab_orchestrator/tests/
```

Or keep a single `tests/` root but group tests into sub-packages that mirror `src/` structure. The current flat layout makes it hard to tell which system a small test covers.

---

## 5. `docs/` — Auto-generated component stubs

The `docs/components/` directory contains many near-identical small markdown files (most 40–55 LoC). They appear to be generated from a single template. Consolidation candidates:

- `docs/components/*.md` (80+ files, ~40–55 LoC each)
- `docs/features/*.md` (under 75 LoC each)
- `docs/archive/*.md` (very short, some 5 LoC)

**Recommendation**: If these are generated, move generation output to `docs/generated/` and delete the per-component pages if they are not linked. Consider replacing the 80+ stub files with a single registry index or a script that generates them on demand.

---

## 6. Broken symlinks to clean up

Three symlinks point to missing targets:

```
/workspace/uq_classification -> src/uqlab/classification
/workspace/uq_benchmarks -> src/uqlab/4_evaluation/benchmarks
/workspace/notebooks/validation/notebook_support
```

**Recommendation**: Remove these broken symlinks. They are not useful and can break tools that traverse the repository.

---

## Proposed Next Steps

1. **Low risk / high cleanup value**: Remove broken symlinks and empty `data/` folder.
2. **Medium risk / structural improvement**: Move `configs/` into `src/uqlab_orchestrator/` or `src/`.
3. **Decision needed**: Determine fate of `uqlab-flask/` (archive, merge, or delete).
4. **Long-term**: Reorganize `tests/` to mirror package structure and consolidate generated docs stubs.

---

## Methodology

Command used to identify candidates:

```bash
find /workspace/<folder> -type f -not -path '*/.git/*' -not -path '*/__pycache__/*' | while read f; do
  lines=$(wc -l < "$f")
  printf "%6d %s\n" "$lines" "$f"
done | sort -n
```

Thresholds: 200 LoC and 300 LoC. Files at or below 300 LoC are reported as "small" and considered relocation candidates.
