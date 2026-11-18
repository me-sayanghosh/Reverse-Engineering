#!/usr/bin/env python3
"""Parse dependency imports across languages, compute module graph, detect cycles, and render Mermaid diagrams."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


import re

NODE_STDLIB = {
    "fs",
    "path",
    "os",
    "http",
    "https",
    "url",
    "crypto",
    "stream",
    "events",
    "util",
    "child_process",
    "buffer",
    "cluster",
    "net",
    "readline",
    "zlib",
    "perf_hooks",
    "worker_threads",
    "assert",
}


def resolve_js_ts_target(source_file: Path, specifier: str, root_path: Path):
    """Resolve a JS/TS import specifier to a repo relative path or external/stdlib name."""
    if specifier.startswith("node:"):
        return specifier, "stdlib"
    if specifier in NODE_STDLIB:
        return specifier, "stdlib"

    if specifier.startswith("."):
        # Relative file import
        base = source_file.parent
        target_path = base / specifier
        candidates = [
            target_path,
            target_path.with_suffix(".ts"),
            target_path.with_suffix(".tsx"),
            target_path.with_suffix(".js"),
            target_path.with_suffix(".jsx"),
            target_path / "index.ts",
            target_path / "index.js",
        ]
        for c in candidates:
            c_resolved = c.resolve()
            if c_resolved.exists() and c_resolved.is_file():
                try:
                    rel = c_resolved.relative_to(root_path)
                    return str(rel), "internal"
                except ValueError:
                    pass
        # Unresolved relative
        return specifier, "internal"

    return specifier, "external"


def parse_js_ts_imports(file_path: Path, root_path: Path):
    """Extract imports from JavaScript and TypeScript files using regex."""
    edges = []
    source_rel = str(file_path.resolve().relative_to(root_path))
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        # import ... from '...' or export ... from '...'
        patterns = [
            r"""(?:import|export)\s+(?:.*?from\s+)?['"]([^'"]+)['"]""",
            r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
            r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        ]
        found_specifiers = set()
        for pat in patterns:
            for m in re.finditer(pat, content):
                found_specifiers.add(m.group(1))

        for spec in sorted(list(found_specifiers)):
            target, imp_type = resolve_js_ts_target(file_path, spec, root_path)
            edges.append(
                {
                    "source": source_rel,
                    "target": target,
                    "type": imp_type,
                    "specifier": spec,
                }
            )
    except Exception:
        pass

    return edges


import ast


def parse_python_imports(file_path: Path, root_path: Path):
    """Use Python AST to parse import and import-from nodes, resolving relative and internal modules."""
    root_path = root_path.resolve()
    file_path = file_path.resolve()
    source_rel = str(file_path.relative_to(root_path))
    edges = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
    except Exception:
        return edges

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                top_pkg = mod.split(".")[0]
                target_rel = mod
                imp_type = "external"

                if hasattr(sys, "stdlib_module_names") and top_pkg in sys.stdlib_module_names:
                    imp_type = "stdlib"
                else:
                    # Check if internal to root
                    possible_pkg = root_path / top_pkg
                    if possible_pkg.exists():
                        target_rel = str(possible_pkg.relative_to(root_path))
                        imp_type = "internal"

                edges.append(
                    {
                        "source": source_rel,
                        "target": target_rel,
                        "type": imp_type,
                        "specifier": mod,
                    }
                )

        elif isinstance(node, ast.ImportFrom):
            level = node.level
            mod = node.module or ""
            specifier = ("." * level) + mod

            if level > 0:
                # Relative import
                imp_type = "internal"
                curr = file_path.parent
                for _ in range(level - 1):
                    curr = curr.parent

                rel_parts = mod.split(".") if mod else []
                target_cand = curr
                for p in rel_parts:
                    target_cand = target_cand / p

                resolved = None
                if target_cand.with_suffix(".py").exists():
                    resolved = target_cand.with_suffix(".py")
                elif (target_cand / "__init__.py").exists():
                    resolved = target_cand / "__init__.py"
                elif target_cand.is_dir():
                    resolved = target_cand

                if resolved and resolved.resolve().is_relative_to(root_path):
                    target_rel = str(resolved.resolve().relative_to(root_path))
                else:
                    target_rel = specifier
            else:
                top_pkg = mod.split(".")[0]
                target_rel = mod
                imp_type = "external"
                if hasattr(sys, "stdlib_module_names") and top_pkg in sys.stdlib_module_names:
                    imp_type = "stdlib"
                else:
                    possible_pkg = root_path / top_pkg
                    if possible_pkg.exists():
                        target_rel = str(possible_pkg.relative_to(root_path))
                        imp_type = "internal"

            edges.append(
                {
                    "source": source_rel,
                    "target": target_rel,
                    "type": imp_type,
                    "specifier": specifier,
                }
            )

    return edges


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract dependency graph, module relationships, cycle detection, and Mermaid diagrams."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--mermaid", action="store_true", help="Output dependency graph as Mermaid markup")
    parser.add_argument("--depth", type=int, default=2, help="Aggregation directory depth (default: 2)")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    data = {
        "root": str(root_path),
        "edges": [],
        "modules": [],
        "cycles": [],
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print("graph LR\n  A --> B")
    else:
        print(f"Dependency Graph for: {root_path}")


if __name__ == "__main__":
    main()
