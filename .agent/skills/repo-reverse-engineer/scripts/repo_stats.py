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
            if d not in _common.DEFAULT_IGNORED_DIRS
            and (not d.startswith(".") or d in (".github", ".circleci", ".gitlab", ".azure-pipelines", ".drone"))
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


def detect_monorepo(root_path: Path):
    """Detect if the repository is a monorepo via workspace configs or multiple manifests."""
    signals = []
    packages = []

    # 1. Workspace config files
    workspace_files = {
        "pnpm-workspace.yaml": "pnpm workspaces",
        "lerna.json": "Lerna",
        "nx.json": "Nx",
        "turbo.json": "Turborepo",
        "go.work": "Go workspaces",
        "MODULE.bazel": "Bazel workspace",
        "WORKSPACE": "Bazel workspace",
    }
    for wf, name in workspace_files.items():
        if (root_path / wf).exists():
            signals.append(f"{name} config detected ({wf})")

    # Discover pnpm workspace packages directly from config
    pnpm_ws = root_path / "pnpm-workspace.yaml"
    if pnpm_ws.exists():
        try:
            content = pnpm_ws.read_text(encoding="utf-8", errors="ignore")
            import re
            for m in re.finditer(r"""-\s*['"]?([a-zA-Z0-9_\-\.\*\/]+)['"]?""", content):
                glob_pat = m.group(1).rstrip("/*")
                cand_dir = root_path / glob_pat
                if cand_dir.exists() and cand_dir.is_dir():
                    for child in cand_dir.iterdir():
                        if child.is_dir() and not child.name.startswith("."):
                            packages.append(str(child.relative_to(root_path)))
        except Exception:
            pass

    # 2. Root manifest checks (package.json workspaces, Cargo.toml [workspace], deno.json workspace)
    pkg_json = root_path / "package.json"
    if pkg_json.exists():
        try:
            import json

            with open(pkg_json, "r", encoding="utf-8") as f:
                pj = json.load(f)
                if "workspaces" in pj:
                    signals.append("npm/yarn/pnpm/bun workspaces in package.json")
                    ws = pj["workspaces"]
                    patterns = ws if isinstance(ws, list) else (ws.get("packages", []) if isinstance(ws, dict) else [])
                    for pat in patterns:
                        cand_dir = root_path / pat.rstrip("/*")
                        if cand_dir.exists() and cand_dir.is_dir():
                            for child in cand_dir.iterdir():
                                if child.is_dir() and not child.name.startswith("."):
                                    packages.append(str(child.relative_to(root_path)))
        except Exception:
            pass

    for dj_name in ["deno.json", "deno.jsonc"]:
        deno_file = root_path / dj_name
        if deno_file.exists():
            try:
                import json
                with open(deno_file, "r", encoding="utf-8") as f:
                    dj = json.load(f)
                    if "workspace" in dj:
                        signals.append(f"Deno workspace in {dj_name}")
                        for mem in dj.get("workspace", []):
                            cand = root_path / mem.rstrip("/*")
                            if cand.exists() and cand.is_dir():
                                packages.append(str(cand.relative_to(root_path)))
            except Exception:
                pass

    cargo_toml = root_path / "Cargo.toml"
    if cargo_toml.exists():
        try:
            content = cargo_toml.read_text(encoding="utf-8", errors="ignore")
            if "[workspace]" in content:
                signals.append("Cargo workspace in Cargo.toml")
                import re
                m_members = re.search(r"""members\s*=\s*\[(.*?)\]""", content, re.DOTALL)
                if m_members:
                    for mem in re.findall(r"""['"]([^'"]+)['"]""", m_members.group(1)):
                        mem_clean = mem.rstrip("/*")
                        cand = root_path / mem_clean
                        if cand.exists() and cand.is_dir():
                            if "*" in mem:
                                for child in cand.iterdir():
                                    if child.is_dir() and not child.name.startswith("."):
                                        packages.append(str(child.relative_to(root_path)))
                            else:
                                packages.append(str(cand.relative_to(root_path)))
        except Exception:
            pass

    # 3. Subfolder manifests
    manifest_names = {
        "package.json",
        "Cargo.toml",
        "pyproject.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
    }
    subfolder_manifests = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in _common.DEFAULT_IGNORED_DIRS
            and (not d.startswith(".") or d in (".github", ".circleci", ".gitlab", ".azure-pipelines", ".drone"))
        ]
        if Path(dirpath) == root_path:
            continue
        for f in filenames:
            if f in manifest_names:
                rel = Path(dirpath).relative_to(root_path)
                subfolder_manifests.append(str(rel / f))
                packages.append(str(rel))

    if len(subfolder_manifests) >= 2:
        signals.append(
            f"Multiple package manifests found in subdirectories ({len(subfolder_manifests)})"
        )

    is_monorepo = len(signals) > 0
    return {
        "is_monorepo": is_monorepo,
        "signals": signals,
        "packages": sorted(list(set(packages))),
    }


def detect_repo_markers(root_path: Path):
    """Detect presence and paths of test directories, documentation, and CI configurations."""
    test_dirs = []
    doc_dirs = []
    ci_paths = []

    # Check common test directory names
    for name in ["tests", "test", "__tests__", "spec", "specs"]:
        p = root_path / name
        if p.exists() and p.is_dir():
            test_dirs.append(name)

    # Check common doc directory names
    for name in ["docs", "doc", "documentation", "wiki"]:
        p = root_path / name
        if p.exists() and p.is_dir():
            doc_dirs.append(name)

    # Check CI configs
    ci_candidates = [
        ".github/workflows",
        ".gitlab-ci.yml",
        ".circleci",
        "Jenkinsfile",
        "azure-pipelines.yml",
        ".travis.yml",
        "bitbucket-pipelines.yml",
    ]
    for ci in ci_candidates:
        p = root_path / ci
        if p.exists():
            ci_paths.append(ci)

    return {
        "tests": {"present": len(test_dirs) > 0, "paths": test_dirs},
        "docs": {"present": len(doc_dirs) > 0, "paths": doc_dirs},
        "ci": {"present": len(ci_paths) > 0, "paths": ci_paths},
    }


def get_git_churn_hints(root_path: Path, top_n: int = 10):
    """If .git has history, return most recently modified files from git log, else empty list."""
    try:
        cmd = ["git", "-C", str(root_path), "log", "-n", "20", "--name-only", "--pretty=format:"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode != 0:
            return []
        recent_files = []
        seen = set()
        for line in res.stdout.splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                if (root_path / line).exists():
                    recent_files.append(line)
                    if len(recent_files) >= top_n:
                        break
        return recent_files
    except Exception:
        return []


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
        if name in ("dockerfile", "containerfile"):
            lang = "Docker"
        elif name == "makefile":
            lang = "Makefile"
        elif name == "cmakelists.txt":
            lang = "C/C++"
        elif name in ("gemfile", "rakefile", "podfile", "vagrantfile"):
            lang = "Ruby"
        elif not ext:
            lang = "Other"
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    first_line = f.readline().strip()
                if first_line.startswith("#!"):
                    fl_lower = first_line.lower()
                    if "python" in fl_lower:
                        lang = "Python"
                    elif "node" in fl_lower or "deno" in fl_lower or "bun" in fl_lower:
                        lang = "JavaScript"
                    elif any(sh in fl_lower for sh in ["bash", "sh", "zsh"]):
                        lang = "Shell"
                    elif "ruby" in fl_lower:
                        lang = "Ruby"
                    elif "perl" in fl_lower:
                        lang = "Perl"
                    elif "php" in fl_lower:
                        lang = "PHP"
                    elif "julia" in fl_lower:
                        lang = "Julia"
                    elif "elixir" in fl_lower:
                        lang = "Elixir"
                    elif "lua" in fl_lower:
                        lang = "Lua"
            except Exception:
                pass
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
    recent_files = get_git_churn_hints(root_path, top_n=10)
    markers = detect_repo_markers(root_path)
    monorepo = detect_monorepo(root_path)

    data = {
        "root": str(root_path),
        "languages": languages,
        "tree": tree_summary,
        "largest_files": largest_files,
        "recently_modified": recent_files,
        "markers": markers,
        "monorepo": monorepo,
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

        if largest_files:
            print("\nLargest Source Files (by lines):")
            print(f"{'Lines':>8}  {'Language':<15} {'Path'}")
            print("-" * 60)
            for lf in largest_files:
                print(f"{lf['lines']:>8}  {lf['language']:<15} {lf['path']}")

        print("\nRepository Markers:")
        t_stat = "Yes (" + ", ".join(markers['tests']['paths']) + ")" if markers['tests']['present'] else "No"
        d_stat = "Yes (" + ", ".join(markers['docs']['paths']) + ")" if markers['docs']['present'] else "No"
        c_stat = "Yes (" + ", ".join(markers['ci']['paths']) + ")" if markers['ci']['present'] else "No"
        print(f"  Tests: {t_stat}")
        print(f"  Docs:  {d_stat}")
        print(f"  CI:    {c_stat}")

        if monorepo["is_monorepo"]:
            print(f"\nMonorepo Detected: Yes ({len(monorepo['packages'])} packages)")
            for sig in monorepo["signals"]:
                print(f"  - {sig}")
        else:
            print("\nMonorepo: No")

        if recent_files:
            print(f"\nRecently Modified Files (Git Churn, top {len(recent_files)}):")
            for rf in recent_files:
                print(f"  - {rf}")


if __name__ == "__main__":
    main()
