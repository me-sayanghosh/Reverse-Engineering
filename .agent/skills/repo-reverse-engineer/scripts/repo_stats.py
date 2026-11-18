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


def get_tree_summary(root_path: Path, max_depth: int = 3):
    """Summarize directory tree up to max_depth with file counts per directory."""
    tree = {}
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune ignored directories
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _common.DEFAULT_IGNORED_DIRS and not d.startswith(".")
        ]

        rel = Path(dirpath).relative_to(root_path)
        depth = 0 if str(rel) == "." else len(rel.parts)
        if depth > max_depth:
            continue

        valid_files = [
            f
            for f in filenames
            if not _common.is_lockfile(f) and not _common.is_minified(f)
        ]

        rel_str = "." if str(rel) == "." else str(rel)
        tree[rel_str] = {
            "depth": depth,
            "files": len(valid_files),
            "subdirs": len(dirnames),
        }

    return tree


def get_largest_files(root_path: Path, top_n: int = 15):
    """List top N largest source files by lines, sorted descending."""
    files_with_lines = []
    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
            rel_path = str(file_path.relative_to(root_path))
            ext = file_path.suffix.lower()
            lang = _common.EXT_TO_LANG.get(ext, "Other")
            files_with_lines.append(
                {"path": rel_path, "lines": lines, "language": lang}
            )
        except Exception:
            pass

    files_with_lines.sort(key=lambda x: x["lines"], reverse=True)
    return files_with_lines[:top_n]


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
    tree_summary = get_tree_summary(root_path, max_depth=3)
    largest_files = get_largest_files(root_path, top_n=15)

    data = {
        "root": str(root_path),
        "languages": languages,
        "tree": tree_summary,
        "largest_files": largest_files,
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

        print("\nDirectory Tree (Depth <= 3):")
        for d, s in tree_summary.items():
            indent = "  " * s["depth"]
            name = d if s["depth"] == 0 else Path(d).name
            print(f"{indent}- {name}/ ({s['files']} files, {s['subdirs']} subdirs)")


if __name__ == "__main__":
    main()
