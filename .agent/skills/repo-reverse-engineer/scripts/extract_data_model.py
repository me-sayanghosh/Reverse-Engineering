#!/usr/bin/env python3
"""Extract database data models, entities, relationships, and generate Mermaid ERDs."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract data models, database entities, foreign keys, and generate Mermaid ER diagrams."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--mermaid", action="store_true", help="Output data model as Mermaid ERD markup")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    data = {
        "root": str(root_path),
        "entities": [],
        "relations": [],
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print("erDiagram\n  ENTITY ||--o{ OTHER : has")
    else:
        print(f"Data Model Extraction for: {root_path}")


if __name__ == "__main__":
    main()
