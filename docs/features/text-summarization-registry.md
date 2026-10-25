# Text summarization registry

## Problem

UQLab’s image registry (`cifar10`, `fashion_mnist`, …) cannot hold Konvens
preference pairs or MSumBench scored summaries. Those artifacts lived only under
`annotated-news-summaries/outputs/`.

## Solution

PrefSum reads the annotated-news checkpoints. It does not copy the pair files
into a second experiment folder. The checkpoint's ``run_meta.json`` names the
jsonl. MLflow records that same file with ``log_input`` on the training run.

| Piece | Location |
|-------|----------|
| Specs | `uqlab.data.text_registry` (`annotated_news`, `msumbench`) |
| Image specs (unchanged) | `uqlab.data.dataset_registry` |
| Import path | `uqlab.data.datasets.registry` |
| Checkpoints and pair files | `annotated-news-summaries/outputs/` |
| UI | **PrefSum** — `streamlit_app_prefsum.py` (`make run-prefsum`, port 8502); section embedding + DI: [`prefsum/README.md`](../../src/uqlab/ui_components/workflow/prefsum/README.md) |

§0 split + pair rebuild lives in `annotated_pair_data._ArticleSplit`.
DPO training still runs against the annotated-news project venv / checkpoints.

**§0 drop-in:** put Konvens annotation jsonl under `annotated-news-summaries/data/`
(`item_id` + `article`/`preferred`/`d6`/`d7`). PrefSum lists matching files; **Apply &
freeze split** writes `outputs/dpo_splits/article_split.json` then pair folders under
`outputs/dpo_pairs/`. Details: [`prefsum/README.md`](../../src/uqlab/ui_components/workflow/prefsum/README.md).

## PrefSum

One screen: pick a preference-file folder (pair counts + MLflow register per set), start or continue a checkpoint (**continue trains every adapter** on its own pair file, then evaluates), show all-adapter score tables, and compare two checkpoints on one test article. For **LLM coverage**, PrefSum can extract article key facts (FeedSum) and show per-summary covered / missing facts plus a short rationale.

**Train/test leak check:** PrefSum compares each checkpoint’s training-pair article ids to ``article_split.json``’s test set. Held-out full / size-matched should show **0%** overlap. All-data training typically overlaps **~83%** of the test articles; those rows are marked **LEAK**, sorted after clean runs, and individual articles used in training are flagged when comparing two checkpoints.

```bash
cd uqlab-streamlit
make run-prefsum
# → http://localhost:8502
```

The classification progressive app stays on `streamlit_app_progressive.py` / `make run-frontend`.
The plain held-out score page in annotated-news (`apps/checkpoint_eval_server.py`, :7860) is optional; PrefSum covers pair + checkpoint management.
