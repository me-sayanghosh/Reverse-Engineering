#!/usr/bin/env python3
"""Locate and rank entrypoints: server bootstraps, CLI commands, route trees, workers, frontend roots."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


def parse_args():
    parser = argparse.ArgumentParser(
        description="Locate and rank application entrypoints, server bootstraps, routes, and workers with citations."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    data = {
        "root": str(root_path),
        "entrypoints": [],
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Entrypoint Discovery for: {root_path}")


if __name__ == "__main__":
    main()
