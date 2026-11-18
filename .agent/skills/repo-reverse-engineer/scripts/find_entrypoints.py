#!/usr/bin/env python3
"""Locate and rank entrypoints: server bootstraps, CLI commands, route trees, workers, frontend roots."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


def find_manifest_entrypoints(root_path: Path):
    """Find entrypoints explicitly declared in package manifests or canonical binary paths."""
    root_path = Path(root_path).resolve()
    entries = []

    # 1. Node / package.json
    for file_path in _common.walk_repo(root_path):
        if file_path.name == "package.json":
            try:
                import json

                with open(file_path, "r", encoding="utf-8") as f:
                    pj = json.load(f)
                    base_dir = file_path.parent
                    rel_base = base_dir.relative_to(root_path)

                    # main field
                    if "main" in pj:
                        main_file = (base_dir / pj["main"]).resolve()
                        if main_file.exists():
                            rel_main = str(main_file.relative_to(root_path))
                            entries.append(
                                {
                                    "path": f"{rel_main}:1",
                                    "type": "main",
                                    "confidence": 1.0,
                                    "reason": f'Declared as "main" in {file_path.relative_to(root_path)}',
                                }
                            )

                    # bin field
                    if "bin" in pj:
                        bin_val = pj["bin"]
                        if isinstance(bin_val, str):
                            bin_file = (base_dir / bin_val).resolve()
                            if bin_file.exists():
                                entries.append(
                                    {
                                        "path": f"{bin_file.relative_to(root_path)}:1",
                                        "type": "cli",
                                        "confidence": 1.0,
                                        "reason": f'Declared as "bin" in {file_path.relative_to(root_path)}',
                                    }
                                )
                        elif isinstance(bin_val, dict):
                            for bname, bpath in bin_val.items():
                                bin_file = (base_dir / bpath).resolve()
                                if bin_file.exists():
                                    entries.append(
                                        {
                                            "path": f"{bin_file.relative_to(root_path)}:1",
                                            "type": "cli",
                                            "confidence": 1.0,
                                            "reason": f'CLI command "{bname}" in {file_path.relative_to(root_path)}',
                                        }
                                    )
            except Exception:
                pass

    # 2. Python __main__.py or pyproject.toml scripts
    for file_path in _common.walk_repo(root_path):
        if file_path.name == "__main__.py":
            entries.append(
                {
                    "path": f"{file_path.relative_to(root_path)}:1",
                    "type": "main",
                    "confidence": 1.0,
                    "reason": "Canonical Python __main__.py module entrypoint",
                }
            )

    pyproject = root_path / "pyproject.toml"
    if pyproject.exists():
        try:
            import re

            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            # match [project.scripts] or [tool.poetry.scripts]
            in_scripts = False
            for idx, line in enumerate(content.splitlines(), start=1):
                if line.strip().startswith("[project.scripts]") or line.strip().startswith("[tool.poetry.scripts]"):
                    in_scripts = True
                    continue
                elif in_scripts and line.strip().startswith("["):
                    in_scripts = False
                    continue
                if in_scripts and "=" in line:
                    cmd_name, target = line.split("=", 1)
                    entries.append(
                        {
                            "path": f"pyproject.toml:{idx}",
                            "type": "cli",
                            "confidence": 1.0,
                            "reason": f"CLI command '{cmd_name.strip()}' declared in pyproject.toml",
                        }
                    )
        except Exception:
            pass

    # 3. Go: cmd/*/main.go or main.go
    for file_path in _common.walk_repo(root_path):
        if file_path.suffix == ".go":
            rel = file_path.relative_to(root_path)
            parts = rel.parts
            if (len(parts) >= 3 and parts[0] == "cmd" and parts[-1] == "main.go") or (
                len(parts) == 1 and parts[0] == "main.go"
            ):
                entries.append(
                    {
                        "path": f"{rel}:1",
                        "type": "main",
                        "confidence": 1.0,
                        "reason": "Go main package entrypoint",
                    }
                )

    # 4. Rust: src/main.rs or src/bin/*.rs
    for file_path in _common.walk_repo(root_path):
        if file_path.suffix == ".rs":
            rel = file_path.relative_to(root_path)
            parts = rel.parts
            if (len(parts) == 2 and parts[0] == "src" and parts[1] == "main.rs") or (
                len(parts) >= 3 and parts[0] == "src" and parts[1] == "bin"
            ):
                entries.append(
                    {
                        "path": f"{rel}:1",
                        "type": "main",
                        "confidence": 1.0,
                        "reason": "Rust binary crate entrypoint",
                    }
                )

    # 5. Java Main methods
    for file_path in _common.walk_repo(root_path):
        if file_path.suffix in (".java", ".kt"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        if "public static void main" in line or "fun main(" in line:
                            entries.append(
                                {
                                    "path": f"{file_path.relative_to(root_path)}:{idx}",
                                    "type": "main",
                                    "confidence": 1.0,
                                    "reason": "Java/Kotlin static main method",
                                }
                            )
                            break
            except Exception:
                pass

    return entries


BOOTSTRAP_PATTERNS = [
    (r"app\.listen\s*\(", "Express/Node app.listen bootstrap"),
    (r"createServer\s*\(", "Node http.createServer bootstrap"),
    (r"uvicorn\.run\s*\(", "Python uvicorn.run ASGI bootstrap"),
    (r"app\.run\s*\(", "Flask/Python app.run server bootstrap"),
    (r"http\.ListenAndServe\s*\(", "Go http.ListenAndServe server bootstrap"),
    (r"@SpringBootApplication", "Spring Boot application bootstrap"),
    (r"HttpServer::new\s*\(", "Rust Actix-web server bootstrap"),
    (r"axum::serve\s*\(", "Rust Axum server bootstrap"),
]


def find_server_bootstraps(root_path: Path):
    """Detect server bootstrap invocations and entrypoint listeners."""
    root_path = Path(root_path).resolve()
    entries = []
    import re

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (
            ".js",
            ".ts",
            ".mjs",
            ".py",
            ".go",
            ".java",
            ".kt",
            ".rs",
            ".rb",
            ".php",
        ):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat, desc in BOOTSTRAP_PATTERNS:
                        if re.search(pat, line):
                            rel = file_path.relative_to(root_path)
                            entries.append(
                                {
                                    "path": f"{rel}:{idx}",
                                    "type": "server",
                                    "confidence": 0.9,
                                    "reason": desc,
                                }
                            )
                            break
        except Exception:
            pass

    return entries


ROUTE_PATTERNS = [
    r"(?:app|router|fastify|server)\.(?:get|post|put|delete|patch|all)\s*\(",
    r"@(?:app|router|api)\.(?:get|post|put|delete|patch|route)\s*\(",
    r"(?:r|router|app|g|api)\.(?:GET|POST|PUT|DELETE|PATCH)\s*\(",
    r"@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(",
    r"(?:get|post|put|delete|patch|resources)\s+['\":/]",
]


def find_route_definitions(root_path: Path):
    """Detect HTTP route definitions and aggregate count per file."""
    root_path = Path(root_path).resolve()
    entries = []
    import re

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (
            ".js",
            ".ts",
            ".mjs",
            ".py",
            ".go",
            ".java",
            ".kt",
            ".rs",
            ".rb",
            ".php",
        ):
            continue

        route_count = 0
        first_line = None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat in ROUTE_PATTERNS:
                        if re.search(pat, line):
                            route_count += 1
                            if first_line is None:
                                first_line = idx
                            break
        except Exception:
            pass

        if route_count > 0:
            rel = file_path.relative_to(root_path)
            entries.append(
                {
                    "path": f"{rel}:{first_line}",
                    "type": "route",
                    "confidence": 0.85,
                    "route_count": route_count,
                    "reason": f"Defines {route_count} HTTP route handler(s)",
                }
            )

    return entries


CLI_WORKER_PATTERNS = [
    # CLI
    (r"argparse\.ArgumentParser\(", "cli", "Python argparse CLI parser"),
    (r"@click\.command\(", "cli", "Python click CLI command"),
    (r"typer\.Typer\(|@app\.command\(", "cli", "Python typer CLI command"),
    (r"require\(['\"]commander['\"]\)|from ['\"]commander['\"]", "cli", "Node Commander CLI"),
    (r"require\(['\"]yargs['\"]\)|from ['\"]yargs['\"]", "cli", "Node Yargs CLI"),
    (r"cobra\.Command\{", "cli", "Go Cobra CLI command"),
    (r"#\[derive\(Parser\)\]|clap::Parser", "cli", "Rust Clap CLI parser"),
    # Workers & Queues
    (r"@(?:celery|app)\.task|Celery\s*\(", "worker", "Python Celery asynchronous task/worker"),
    (r"new (?:Worker|Queue)\s*\(", "worker", "Node Bull/BullMQ background queue/worker"),
    (r"include Sidekiq::Worker", "worker", "Ruby Sidekiq background worker"),
    (r"cron\.schedule\s*\(|@Scheduled\(|@cron", "worker", "Scheduled / cron background task"),
]


def find_cli_and_workers(root_path: Path):
    """Detect CLI command parsers and background worker/queue patterns."""
    root_path = Path(root_path).resolve()
    entries = []
    import re

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (
            ".js",
            ".ts",
            ".mjs",
            ".py",
            ".go",
            ".java",
            ".kt",
            ".rs",
            ".rb",
            ".php",
        ):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for idx, line in enumerate(f, start=1):
                    for pat, etype, desc in CLI_WORKER_PATTERNS:
                        if re.search(pat, line):
                            rel = file_path.relative_to(root_path)
                            entries.append(
                                {
                                    "path": f"{rel}:{idx}",
                                    "type": etype,
                                    "confidence": 0.85,
                                    "reason": desc,
                                }
                            )
                            break
        except Exception:
            pass

    return entries


def find_frontend_entrypoints(root_path: Path):
    """Detect frontend SPA, Next.js, and static web entrypoint roots."""
    root_path = Path(root_path).resolve()
    entries = []

    frontend_targets = [
        ("index.html", "Static HTML web entrypoint"),
        ("src/main.tsx", "React/Vite main TSX root"),
        ("src/main.jsx", "React/Vite main JSX root"),
        ("src/index.tsx", "React main TSX root"),
        ("src/index.jsx", "React main JSX root"),
        ("src/App.tsx", "Root React App component"),
        ("src/App.jsx", "Root React App component"),
        ("src/App.vue", "Root Vue App component"),
        ("src/App.svelte", "Root Svelte App component"),
        ("app/layout.tsx", "Next.js App Router root layout"),
        ("app/page.tsx", "Next.js App Router home page"),
        ("pages/_app.tsx", "Next.js Pages Router custom app"),
        ("pages/index.tsx", "Next.js Pages Router index page"),
        ("vite.config.ts", "Vite build configuration entrypoint"),
        ("vite.config.js", "Vite build configuration entrypoint"),
    ]

    for rel_str, desc in frontend_targets:
        target_file = root_path / rel_str
        if target_file.exists():
            entries.append(
                {
                    "path": f"{rel_str}:1",
                    "type": "frontend",
                    "confidence": 0.85,
                    "reason": desc,
                }
            )

    return entries


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

    manifest_entries = find_manifest_entrypoints(root_path)
    bootstrap_entries = find_server_bootstraps(root_path)
    route_entries = find_route_definitions(root_path)
    cli_worker_entries = find_cli_and_workers(root_path)
    frontend_entries = find_frontend_entrypoints(root_path)

    all_entries = (
        manifest_entries
        + bootstrap_entries
        + route_entries
        + cli_worker_entries
        + frontend_entries
    )

    data = {
        "root": str(root_path),
        "entrypoints": all_entries,
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Entrypoint Discovery for: {root_path}")
        for ep in manifest_entries:
            print(f"[{ep['type']}] {ep['path']} (confidence: {ep['confidence']}) - {ep['reason']}")


if __name__ == "__main__":
    main()
