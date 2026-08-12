#!/usr/bin/env python3
"""Scan top-level folders and report small-file relocation candidates.

A root folder is considered a candidate when every file inside it is smaller
than a configurable LoC threshold (default 200 and 300). The script also
records which files in the repository reference the candidate folder, so the
report can judge whether the folder is self-contained enough to move.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


def _iter_files(root: Path) -> list[Path]:
    """Return all non-hidden files under ``root`` (ignoring __pycache__)."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        files.append(path)
    return files


def count_loc(path: Path) -> int:
    """Return the number of lines in a text file (0 for unreadable files)."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return len(fh.readlines())
    except (OSError, UnicodeDecodeError):
        return 0


def find_references(
    folder_name: str, repo_root: Path, ignore_paths: set[str] | None = None
) -> dict[str, list[str]]:
    """Find files that mention ``folder_name/`` as a path or import anchor."""
    refs: dict[str, list[str]] = defaultdict(list)
    needle = f"{folder_name}/"
    ignore_paths = ignore_paths or set()

    for path in _iter_files(repo_root):
        # Skip the candidate folder itself, this script, and its output report.
        if folder_name in path.parts[: len(path.parts)]:
            continue
        if str(path.resolve()) in ignore_paths:
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pt", ".pth", ".bin"}:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if needle in line or f'"{folder_name}"' in line or f"'{folder_name}'" in line:
                        refs[str(path)].append(f"{i}: {line.strip()}")
        except (OSError, UnicodeDecodeError):
            continue
    return refs


def analyze_folder(folder: Path, repo_root: Path, threshold: int) -> dict | None:
    """Analyze a single top-level folder against a LoC threshold."""
    files = _iter_files(folder)
    if not files:
        return None

    locs = [(f, count_loc(f)) for f in files]
    small = [(f, loc) for f, loc in locs if loc < threshold]
    large = [(f, loc) for f, loc in locs if loc >= threshold]

    return {
        "folder": folder,
        "total": len(files),
        "small": small,
        "large": large,
        "all_small": len(small) == len(files),
        "mostly_small": len(small) / len(files) >= 0.8,
    }


def build_report(repo_root: Path, thresholds: list[int], output_path: Path) -> str:
    """Build a Markdown report of relocation candidates."""
    lines = [
        "# Small-file relocation candidates",
        "",
        "This report lists top-level folders whose files are all below the given LoC thresholds,",
        "and assesses whether they can be relocated without breaking consumers.",
        "",
        f"Generated from: `{repo_root}`",
        "",
    ]

    candidates = sorted(
        d for d in repo_root.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    # Summary table with fixed LoC buckets.
    lines.append("## Summary")
    lines.append("")
    lines.append("| Folder | Total files | < 200 LoC | 200-300 LoC | > 300 LoC |")
    lines.append("|--------|-------------|-----------|-------------|-----------|")

    for folder in candidates:
        files = _iter_files(folder)
        if not files:
            lines.append(f"| `{folder.name}` | 0 | - | - | - |")
            continue
        locs = [count_loc(f) for f in files]
        total = len(locs)
        small = sum(1 for loc in locs if loc < 200)
        medium = sum(1 for loc in locs if 200 <= loc < 300)
        large = sum(1 for loc in locs if loc >= 300)
        lines.append(
            f"| `{folder.name}` | {total} | {small} | {medium} | {large} |"
        )

    lines.append("")
    lines.append(f"*Thresholds considered: {', '.join(map(str, thresholds))} LoC.*")

    # Candidate details.
    lines.append("")
    lines.append("## Candidate details")
    lines.append("")

    candidate_threshold = min(thresholds)

    for folder in candidates:
        analysis = analyze_folder(folder, repo_root, candidate_threshold)
        if not analysis or not analysis["all_small"]:
            continue

        lines.append(f"### `{folder.name}/`")
        lines.append("")
        lines.append(
            f"- **All files under {candidate_threshold} LoC:** {analysis['total']}/{analysis['total']}"
        )
        lines.append(f"- **Location:** `{folder.relative_to(repo_root)}`")

        # File listing with LoC.
        lines.append("")
        lines.append("| Lines | File |")
        lines.append("|-------|------|")
        for f, loc in sorted(analysis["small"], key=lambda x: x[1]):
            rel = f.relative_to(repo_root)
            lines.append(f"| {loc} | `{rel}` |")

        # Consumer references.
        script_path = Path(__file__).resolve()
        ignore_paths = {str(script_path), str(output_path.resolve())}
        refs = find_references(folder.name, repo_root, ignore_paths=ignore_paths)
        lines.append("")
        if refs:
            lines.append("**Consumers (references found):**")
            lines.append("")
            for ref_path, snippets in sorted(refs.items()):
                lines.append(f"- `{ref_path}`")
                for snippet in snippets[:3]:
                    lines.append(f"  - `{snippet}`")
                if len(snippets) > 3:
                    lines.append(f"  - ... and {len(snippets) - 3} more")
        else:
            lines.append("**Consumers:** None found outside the folder itself.")

        lines.append("")
        lines.append("**Movability assessment:**")
        if not refs:
            lines.append(
                "- ✅ Can be moved freely; no external references detected."
            )
        elif len(refs) == 1:
            lines.append(
                "- ⚠️  One consumer references this folder. Move only after updating it."
            )
        else:
            lines.append(
                f"- ⚠️  {len(refs)} consumers reference this folder. Moving requires updating all of them."
            )

        # Suggest destination based on content.
        if folder.name == "configs":
            lines.append(
                "- Suggested destination: `src/uqlab_core/configs/` as package data, "
                "or keep at root if YAML configs remain a user-facing entry point."
            )
        elif folder.name == "uqlab-flask":
            lines.append(
                "- Suggested destination: `backend/` or `src/uqlab_core/api/flask/` "
                "if the Flask app is intended to merge with the main backend."
            )
        elif folder.name == "data":
            lines.append(
                "- Suggested destination: Keep at root; it is a persistent data mount "
                "referenced by `runtime_paths.data_root()`."
            )
        else:
            lines.append(
                "- Suggested destination: evaluate whether the folder fits into "
                "`scripts/`, `src/`, or `backend/` based on its consumers."
            )
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze small root folders for relocation")
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="Repository root (default: .)"
    )
    parser.add_argument(
        "--thresholds", nargs="+", type=int, default=[200, 300], help="LoC thresholds (default: 200 300)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("SMALL_FILE_RELOCATION_CANDIDATES.md"), help="Output Markdown file"
    )
    args = parser.parse_args()

    repo_root = args.root.resolve()
    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    report = build_report(repo_root, args.thresholds, output_path)

    args.output.write_text(report, encoding="utf-8")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
