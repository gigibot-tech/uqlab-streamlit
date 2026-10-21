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
| UI | **PrefSum** — `streamlit_app_prefsum.py` (`make run-prefsum`, port 8502) |

Pair construction and DPO training stay in `annotated-news-summaries/features/`.
PrefSum only reads them.

## PrefSum

One screen: choose a checkpoint, read the set table (name, pair count, jsonl path), open one chosen/rejected pair from that file, and show saved test scores when a means file exists.

```bash
cd uqlab-streamlit
make run-prefsum
# → http://localhost:8502
```

The classification progressive app stays on `streamlit_app_progressive.py` / `make run-frontend`.
The plain held-out score page in annotated-news (`apps/checkpoint_eval_server.py`, :7860) is optional; PrefSum covers pair + checkpoint management.
