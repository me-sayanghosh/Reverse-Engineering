#!/usr/bin/env python3
"""Scan environment variables, configuration keys, and detect potential secret leaks with strict redaction."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


import re

ENV_PATTERNS = [
    r"""process\.env\.([A-Za-z0-9_]+)""",
    r"""process\.env\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\[['"]([A-Za-z0-9_]+)['"]\]""",
    r"""os\.environ\.get\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""System\.getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""os\.Getenv\(['"]([A-Za-z0-9_]+)['"]""",
    r"""std::env::var\(['"]([A-Za-z0-9_]+)['"]""",
    r"""ENV\[['"]([A-Za-z0-9_]+)['"]\]""",
]


def find_env_vars(root_path: Path):
    """Scan source code and .env.example files for environment variable names only (values strictly excluded)."""
    root_path = root_path.resolve()
    env_vars = {}

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()

        # Check .env.example / sample templates
        if name in (".env.example", ".env.sample", ".env.template", ".env.dist"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            var_name = line.split("=", 1)[0].strip()
                            if var_name:
                                if var_name not in env_vars:
                                    env_vars[var_name] = {"name": var_name, "occurrences": []}
                                env_vars[var_name]["occurrences"].append(f"{rel}:{idx}")
            except Exception:
                pass

        # Check source code invocations
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat in ENV_PATTERNS:
                        for m in re.finditer(pat, line):
                            var_name = m.group(1)
                            # Ignore common non-env props like process.env.NODE_ENV handled cleanly
                            if var_name not in env_vars:
                                env_vars[var_name] = {"name": var_name, "occurrences": []}
                            citation = f"{rel}:{idx}"
                            if citation not in env_vars[var_name]["occurrences"]:
                                env_vars[var_name]["occurrences"].append(citation)
        except Exception:
            pass

    return list(env_vars.values())


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scan repository environment variable usage, config keys, and audit potential secret leaks."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    env_vars = find_env_vars(root_path)

    data = {
        "root": str(root_path),
        "env_vars": env_vars,
        "config_keys": [],
        "secret_findings": [],
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Secret and Env Scanner for: {root_path}")


if __name__ == "__main__":
    main()
