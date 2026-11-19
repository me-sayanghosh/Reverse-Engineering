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
    "test",
    "wasi",
    "diagnostics_channel",
    "async_hooks",
    "v8",
    "vm",
    "string_decoder",
    "timers",
    "tls",
    "dgram",
    "dns",
    "punycode",
    "constants",
    "inspector",
    "trace_events",
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
            target_path / "index.tsx",
            target_path / "index.js",
            target_path / "index.jsx",
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
            r"""(?:import|export)\s+(?:(?:(?!\b(?:import|export)\b).)*?\bfrom\s+)?['"]([^'"]+)['"]""",
            r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""",
            r"""import\s*\(\s*['"]([^'"]+)['"]\s*\)""",
        ]
        found_specifiers = set()
        for pat in patterns:
            for m in re.finditer(pat, content, re.DOTALL):
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

                if not mod:
                    # from . import foo, bar
                    for alias in node.names:
                        sub_cand = curr / alias.name
                        resolved = None
                        if sub_cand.with_suffix(".py").exists():
                            resolved = sub_cand.with_suffix(".py")
                        elif (sub_cand / "__init__.py").exists():
                            resolved = sub_cand / "__init__.py"
                        elif sub_cand.is_dir():
                            resolved = sub_cand

                        if resolved and resolved.resolve().is_relative_to(root_path):
                            target_rel = str(resolved.resolve().relative_to(root_path))
                        else:
                            target_rel = f"{'.' * level}{alias.name}"

                        edges.append(
                            {
                                "source": source_rel,
                                "target": target_rel,
                                "type": imp_type,
                                "specifier": f"{'.' * level}{alias.name}",
                            }
                        )
                    continue

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


def parse_go_imports(file_path: Path, root_path: Path, go_module: str = ""):
    """Parse Go imports and resolve to internal if matching the module path."""
    edges = []
    source_rel = str(file_path.resolve().relative_to(root_path))
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # Match single line or block imports (including aliased imports)
    single_imports = re.findall(r'import\s+(?:[a-zA-Z0-9_.]+\s+)?"([^"]+)"', content)
    block_matches = re.findall(r"import\s*\(\s*(.*?)\s*\)", content, re.DOTALL)
    all_imports = list(single_imports)
    for block in block_matches:
        for line in block.splitlines():
            m = re.search(r'"([^"]+)"', line)
            if m:
                all_imports.append(m.group(1))

    for imp in all_imports:
        if go_module and imp.startswith(go_module):
            subpath = imp[len(go_module) :].lstrip("/")
            edges.append(
                {
                    "source": source_rel,
                    "target": subpath or imp,
                    "type": "internal",
                    "specifier": imp,
                }
            )
        elif "/" not in imp:
            edges.append(
                {
                    "source": source_rel,
                    "target": imp,
                    "type": "stdlib",
                    "specifier": imp,
                }
            )
        else:
            edges.append(
                {
                    "source": source_rel,
                    "target": imp,
                    "type": "external",
                    "specifier": imp,
                }
            )
    return edges


def parse_rust_imports(file_path: Path, root_path: Path):
    """Parse Rust use statements and resolve crate::/super:: to internal."""
    edges = []
    source_rel = str(file_path.resolve().relative_to(root_path))
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    matches = re.findall(r"use\s+([^;]+);", content)
    for m in matches:
        raw = m.strip()
        if raw.startswith("crate::") or raw.startswith("super::"):
            # Internal
            sub = raw.replace("crate::", "").replace("super::", "").split("::")[0]
            edges.append(
                {
                    "source": source_rel,
                    "target": f"src/{sub}",
                    "type": "internal",
                    "specifier": raw,
                }
            )
        elif raw.startswith("std::") or raw.startswith("core::"):
            edges.append(
                {
                    "source": source_rel,
                    "target": raw.split("::")[0],
                    "type": "stdlib",
                    "specifier": raw,
                }
            )
        else:
            edges.append(
                {
                    "source": source_rel,
                    "target": raw.split("::")[0],
                    "type": "external",
                    "specifier": raw,
                }
            )
    return edges


def parse_java_imports(file_path: Path, root_path: Path, pkg_prefix: str = ""):
    """Parse Java/Kotlin imports and mark internal if matching local package prefix."""
    edges = []
    source_rel = str(file_path.resolve().relative_to(root_path))
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    matches = re.findall(r"import\s+([a-zA-Z0-9_.]+);", content)
    for raw in matches:
        if raw.startswith("java.") or raw.startswith("javax."):
            imp_type = "stdlib"
        elif pkg_prefix and raw.startswith(pkg_prefix):
            imp_type = "internal"
        else:
            imp_type = "external"
        edges.append(
            {
                "source": source_rel,
                "target": raw,
                "type": imp_type,
                "specifier": raw,
            }
        )
    return edges


def collect_all_imports(root_path: Path):
    """Walk repository and collect all dependency edges across all supported languages."""
    root_path = root_path.resolve()
    all_edges = []

    # Detect Go module name if present
    go_module = ""
    go_mod_file = root_path / "go.mod"
    if go_mod_file.exists():
        try:
            m = re.search(
                r"^module\s+([^\s]+)",
                go_mod_file.read_text(encoding="utf-8", errors="ignore"),
                re.MULTILINE,
            )
            if m:
                go_module = m.group(1).strip()
        except Exception:
            pass

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()

        if ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
            all_edges.extend(parse_js_ts_imports(file_path, root_path))
        elif ext in (".py", ".pyi"):
            all_edges.extend(parse_python_imports(file_path, root_path))
        elif ext == ".go":
            all_edges.extend(parse_go_imports(file_path, root_path, go_module))
        elif ext == ".rs":
            all_edges.extend(parse_rust_imports(file_path, root_path))
        elif ext in (".java", ".kt"):
            all_edges.extend(parse_java_imports(file_path, root_path))

    return all_edges


def get_module_name(file_rel: str, depth: int = 2) -> str:
    """Map a file path to its module directory at given depth."""
    parts = Path(file_rel).parts
    if len(parts) <= 1:
        return "."
    mod_parts = parts[: min(depth, len(parts) - 1)]
    return "/".join(mod_parts) if mod_parts else "."


def aggregate_module_edges(edges: list, depth: int = 2):
    """Collapse internal file-level edges to directory/package-level modules."""
    module_edges = {}
    modules = set()

    for edge in edges:
        if edge["type"] != "internal":
            continue
        src = edge["source"]
        tgt = edge["target"]
        mod_src = get_module_name(src, depth)
        mod_tgt = get_module_name(tgt, depth)

        modules.add(mod_src)
        modules.add(mod_tgt)

        if mod_src != mod_tgt:
            key = (mod_src, mod_tgt)
            module_edges[key] = module_edges.get(key, 0) + 1

    result_edges = [
        {"source": src, "target": tgt, "weight": weight}
        for (src, tgt), weight in module_edges.items()
    ]
    return sorted(list(modules)), result_edges


def compute_centrality_and_cycles(modules: list, edges: list):
    """Compute in/out degrees, top central modules, and detect circular dependency cycles."""
    in_degrees = {m: 0 for m in modules}
    out_degrees = {m: 0 for m in modules}
    adj = {m: [] for m in modules}

    for edge in edges:
        src = edge["source"]
        tgt = edge["target"]
        if src in out_degrees:
            out_degrees[src] += 1
        if tgt in in_degrees:
            in_degrees[tgt] += 1
        if src in adj and tgt in adj:
            adj[src].append(tgt)

    centrality = []
    for m in modules:
        in_d = in_degrees.get(m, 0)
        out_d = out_degrees.get(m, 0)
        centrality.append(
            {
                "module": m,
                "in_degree": in_d,
                "out_degree": out_d,
                "total_degree": in_d + out_d,
            }
        )
    centrality.sort(key=lambda x: x["total_degree"], reverse=True)
    top_central = centrality[:10]

    # Cycle detection via DFS
    visited = {}  # 0: unvisited, 1: visiting (in stack), 2: finished
    for m in modules:
        visited[m] = 0

    cycles = []
    path = []

    def dfs(curr):
        visited[curr] = 1
        path.append(curr)

        for neighbor in adj.get(curr, []):
            if visited.get(neighbor) == 1:
                # Cycle found!
                cycle_start_idx = path.index(neighbor)
                cycle_path = path[cycle_start_idx:] + [neighbor]
                cycles.append(cycle_path)
            elif visited.get(neighbor) == 0:
                dfs(neighbor)

        path.pop()
        visited[curr] = 2

    for m in modules:
        if visited[m] == 0:
            dfs(m)

    return top_central, cycles


def sanitize_mermaid_id(name: str) -> str:
    """Create a safe alphanumeric identifier for Mermaid node IDs."""
    import re

    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_")
    return safe or "root"


def render_mermaid_graph(modules: list, edges: list, max_nodes: int = 40) -> str:
    """Emit graph LR Mermaid markup capped at max_nodes."""
    lines = ["graph LR"]

    if not modules:
        lines.append("  Empty[No internal modules detected]")
        return "\n".join(lines)

    # If modules exceed max_nodes, pick top modules and bucket rest into 'other'
    top_modules = set(modules[: max_nodes - 1]) if len(modules) > max_nodes else set(modules)
    has_other = len(modules) > len(top_modules)

    node_ids = {}
    for idx, m in enumerate(sorted(list(top_modules))):
        nid = f"m_{idx}"
        node_ids[m] = nid
        lines.append(f'  {nid}["{m}"]')

    if has_other:
        node_ids["other"] = "m_other"
        lines.append('  m_other["(other modules)"]')

    # Deduplicate aggregated edges
    seen_edges = set()
    for e in edges:
        s = e["source"]
        t = e["target"]
        mod_s = s if s in top_modules else "other"
        mod_t = t if t in top_modules else "other"

        if mod_s == mod_t:
            continue

        nid_s = node_ids.get(mod_s, "m_other")
        nid_t = node_ids.get(mod_t, "m_other")

        edge_key = (nid_s, nid_t)
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            w = e.get("weight")
            if w and w > 1:
                lines.append(f"  {nid_s} -->|{w}| {nid_t}")
            else:
                lines.append(f"  {nid_s} --> {nid_t}")

    return "\n".join(lines)


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

    all_edges = collect_all_imports(root_path)
    modules, module_edges = aggregate_module_edges(all_edges, depth=args.depth)
    centrality, cycles = compute_centrality_and_cycles(modules, module_edges)

    data = {
        "root": str(root_path),
        "total_file_imports": len(all_edges),
        "modules": modules,
        "module_edges": module_edges,
        "centrality": centrality,
        "cycles": cycles,
        "raw_edges": all_edges,
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print(render_mermaid_graph(modules, module_edges, max_nodes=40))
    else:
        print(f"Dependency Graph for: {root_path}")
        print(f"Modules discovered: {len(modules)}")
        print(f"Inter-module dependencies: {len(module_edges)}")
        if cycles:
            print(f"WARNING: Circular dependencies detected ({len(cycles)}):")
            for c in cycles:
                print(f"  {' -> '.join(c)}")
        else:
            print("Circular dependencies: None detected")
        print("\nTop Central Modules:")
        for c in centrality[:5]:
            print(f"  {c['module']}: in={c['in_degree']}, out={c['out_degree']}, total={c['total_degree']}")


if __name__ == "__main__":
    main()
