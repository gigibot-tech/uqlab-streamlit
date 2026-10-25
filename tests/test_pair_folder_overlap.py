"""Selected preference folder × article_split / peer catalogs."""

from __future__ import annotations

import json
from pathlib import Path

from uqlab.summarization.annotated_news import (
    checkpoint_lineage,
    continued_from_label,
    pair_dirs_article_overlap,
    pair_folder_metadata_overlap,
)


def _write_jsonl(path: Path, item_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item_id in item_ids:
            handle.write(json.dumps({"item_id": item_id, "chosen": "a", "rejected": "b"}) + "\n")


def test_pair_folder_metadata_overlap_flags_test_leak(tmp_path: Path) -> None:
    split = {
        "train": ["1", "2", "3"],
        "val": ["4"],
        "test": ["5", "6"],
    }
    (tmp_path / "outputs" / "dpo_splits").mkdir(parents=True)
    (tmp_path / "outputs" / "dpo_splits" / "article_split.json").write_text(
        json.dumps(split), encoding="utf-8"
    )
    clean = tmp_path / "outputs" / "dpo_pairs" / "held_out" / "full"
    leak = tmp_path / "outputs" / "dpo_pairs"
    _write_jsonl(clean / "coverage.jsonl", ["1", "2"])
    _write_jsonl(leak / "coverage.jsonl", ["1", "5"])  # all_data-style test id

    held = pair_folder_metadata_overlap(
        tmp_path, clean, set_names=["coverage"], peer_sources=[]
    )
    assert held["clean"] is True
    assert held["by_set"][0]["∩ test"] == 0
    assert held["by_set"][0]["status"] == "clean"

    leaked = pair_folder_metadata_overlap(
        tmp_path, leak, set_names=["coverage"], peer_sources=[]
    )
    assert leaked["clean"] is False
    assert leaked["by_set"][0]["∩ test"] == 1
    assert leaked["by_set"][0]["status"] == "LEAK"


def test_pair_folder_vs_catalog_jaccard(tmp_path: Path) -> None:
    (tmp_path / "outputs" / "dpo_splits").mkdir(parents=True)
    (tmp_path / "outputs" / "dpo_splits" / "article_split.json").write_text(
        json.dumps({"train": ["1", "2", "3"], "val": [], "test": ["9"]}),
        encoding="utf-8",
    )
    full = tmp_path / "outputs" / "dpo_pairs" / "held_out" / "full"
    matched = tmp_path / "outputs" / "dpo_pairs" / "held_out" / "size_matched" / "seed_2"
    _write_jsonl(full / "joint.jsonl", ["1", "2", "3"])
    _write_jsonl(matched / "joint.jsonl", ["1", "2"])  # subset

    peers = [
        {"label": "held_out/full", "path": full, "counts": {"joint": 3}},
        {"label": "held_out/size_matched/seed_2", "path": matched, "counts": {"joint": 2}},
    ]
    analysis = pair_folder_metadata_overlap(
        tmp_path, matched, set_names=["joint"], peer_sources=peers
    )
    assert len(analysis["vs_catalog"]) == 1
    row = analysis["vs_catalog"][0]
    assert row["shared"] == 2
    assert row["selected_only"] == 0
    assert row["peer_only"] == 1
    assert row["jaccard_%"] == round(100.0 * 2 / 3, 1)


def test_pair_dirs_article_overlap(tmp_path: Path) -> None:
    left = tmp_path / "a"
    right = tmp_path / "b"
    _write_jsonl(left / "faithfulness.jsonl", ["10", "11"])
    _write_jsonl(right / "faithfulness.jsonl", ["11", "12"])
    rows = pair_dirs_article_overlap(left, right, ["faithfulness"])
    assert rows[0]["shared"] == 1
    assert rows[0]["selected_only"] == 1
    assert rows[0]["reference_only"] == 1
    assert rows[0]["jaccard_%"] == round(100.0 / 3, 1)


def test_continued_from_label() -> None:
    assert continued_from_label("run_plus200") == "run"
    assert continued_from_label("run_plus200_plus100") == "run_plus200"
    assert continued_from_label("run") is None


def test_checkpoint_lineage_mermaid(tmp_path: Path) -> None:
    pairs = tmp_path / "outputs" / "dpo_pairs" / "held_out" / "full"
    _write_jsonl(pairs / "coverage.jsonl", ["1"])
    runs = [
        {
            "label": "base_s200",
            "max_steps": 200,
            "learning_rate": 5e-5,
            "pairs_paths": {"coverage": str(pairs / "coverage.jsonl")},
        },
        {
            "label": "base_s200_plus200",
            "max_steps": 200,
            "learning_rate": 5e-5,
            "pairs_paths": {"coverage": str(pairs / "coverage.jsonl")},
        },
    ]
    graph = checkpoint_lineage(tmp_path, runs=runs, pairs_dir=pairs)
    assert graph["continue_edges"] == [{"from": "base_s200", "to": "base_s200_plus200"}]
    assert all(node["uses_selected"] for node in graph["nodes"])
    assert "flowchart TB" in graph["mermaid"]
    assert "plus" in graph["mermaid"]
    assert "held_out/full" in graph["mermaid"]
