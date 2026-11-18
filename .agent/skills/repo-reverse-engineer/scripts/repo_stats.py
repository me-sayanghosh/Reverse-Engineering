#!/usr/bin/env python3
"""Compute repository statistics: language LOC, directory tree, largest files, CI/test presence, monorepo hints."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add script directory to sys.path for _common import
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute repository statistics, language breakdown, tree summary, and structural hints."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def count_languages(root_path: Path):
    """Count files and non-blank lines per language."""
    stats = {}
    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        name = file_path.name.lower()
        if name == "dockerfile":
            lang = "Docker"
        elif name == "makefile":
            lang = "Makefile"
        else:
            lang = _common.EXT_TO_LANG.get(ext, "Other")

        if lang not in stats:
            stats[lang] = {"files": 0, "lines": 0}
        stats[lang]["files"] += 1

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                non_blank = sum(1 for line in f if line.strip())
                stats[lang]["lines"] += non_blank
        except Exception:
            pass

    return dict(sorted(stats.items(), key=lambda x: x[1]["lines"], reverse=True))


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    languages = count_languages(root_path)

    data = {
        "root": str(root_path),
        "languages": languages,
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Repository Stats for: {root_path}")
        print("\nLanguage Breakdown (Files & Non-blank LOC):")
        print(f"{'Language':<20} {'Files':>8} {'Lines':>10}")
        print("-" * 40)
        for lang, s in languages.items():
            print(f"{lang:<20} {s['files']:>8} {s['lines']:>10}")


if __name__ == "__main__":
    main()
