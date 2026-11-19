#!/usr/bin/env python3
"""Shared helper module for repo-reverse-engineer scripts."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Generator

# Directories and patterns to ignore during repository traversal
DEFAULT_IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "vendor",
    "target",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "env",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    "coverage",
    ".nyc_output",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".idea",
    ".vscode",
    "out",
    "bin",
    "obj",
    ".yarn",
    ".pnpm-store",
    ".bundle",
    ".gradle",
    ".cargo",
    "Pods",
    ".dart_tool",
    ".serverless",
    ".terraform",
    "dist-ssr",
    "storybook-static",
    ".angular",
    ".svelte-kit",
    ".docusaurus",
}

LOCKFILES = {
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "Cargo.lock.dist",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Gemfile.lock",
    "go.sum",
    "flake.lock",
    "bun.lockb",
    "bun.lock",
    "mix.lock",
    "pubspec.lock",
    "shard.lock",
}


def is_too_large(path: str | Path, limit_bytes: int = 1024 * 1024) -> bool:
    """Return True if file size exceeds limit_bytes (default 1MB)."""
    try:
        return os.path.getsize(path) > limit_bytes
    except OSError:
        return True


def read_text_safe(path: str | Path, max_bytes: int = 1024 * 1024) -> str:
    """Safely read text from file up to max_bytes, handling encodings, BOMs, and suppressing errors."""
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                return data.decode("utf-16")
            except UnicodeDecodeError:
                return data.decode("latin-1", errors="ignore")
    except OSError:
        return ""


def is_binary(path: str | Path) -> bool:
    """Return True if file appears to be binary based on null bytes, encoding, or control characters."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if not chunk:
                return False
            # Check for UTF-16 BOM text files
            if chunk.startswith((b"\xff\xfe", b"\xfe\xff")):
                try:
                    chunk.decode("utf-16")
                    return False
                except Exception:
                    return True
            if b"\x00" in chunk:
                return True
            # Try decoding as utf-8, handling split multi-byte characters at chunk boundary
            import codecs
            try:
                decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
                decoder.decode(chunk, final=False)
                return False
            except UnicodeDecodeError:
                # Heuristic for non-UTF8 single-byte text files (e.g. Latin-1 / Windows-1252)
                control_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
                non_text = chunk.translate(None, control_chars)
                return (len(non_text) / len(chunk)) > 0.30
    except OSError:
        return True


EXT_TO_LANG: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".dart": "Dart",
    ".lua": "Lua",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".r": "R",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".pl": "Perl",
    ".zig": "Zig",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    ".sol": "Solidity",
    ".tf": "HCL",
    ".tfvars": "HCL",
    ".dockerfile": "Docker",
    ".prisma": "Prisma",
    ".json5": "JSON",
    ".jsonc": "JSON",
    ".astro": "Astro",
    ".svx": "Svelte",
    ".mdx": "Markdown",
    ".wgsl": "WGSL",
    ".jl": "Julia",
    ".clj": "Clojure",
    ".cljs": "Clojure",
    ".cljc": "Clojure",
    ".fs": "F#",
    ".fsi": "F#",
    ".fsx": "F#",
    ".nim": "Nim",
    ".v": "V",
    ".odin": "Odin",
    ".gleam": "Gleam",
}


LOCKFILES_LOWER = {f.lower() for f in LOCKFILES}


def is_lockfile(filename: str) -> bool:
    return filename.lower() in LOCKFILES_LOWER


def is_minified(filename: str | Path) -> bool:
    name = str(filename).replace("\\", "/").split("/")[-1].lower()
    return (
        name.endswith(".min.js")
        or name.endswith(".min.mjs")
        or name.endswith(".min.cjs")
        or name.endswith(".min.css")
        or name.endswith(".bundle.js")
        or name.endswith(".bundle.mjs")
        or name.endswith(".bundle.cjs")
        or name.endswith(".bundle.css")
        or name.endswith(".chunk.js")
        or name.endswith(".chunk.css")
        or name.endswith(".chunk.mjs")
        or name.endswith(".map")
    )


def die(message: str, code: int = 1) -> None:
    """Print error message to stderr and exit with non-zero code."""
    sys.stderr.write(f"ERROR: {message}\n")
    sys.exit(code)


def output_json(data: Any) -> None:
    """Format and print data as indented JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def walk_repo(root: str | Path) -> Generator[Path, None, None]:
    """Walk repository root directory, yielding Path objects for non-ignored regular files."""
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        die(f"Path does not exist: {root_path}")
    if root_path.is_file():
        yield root_path
        return

    def on_walk_error(err: OSError) -> None:
        pass

    for dirpath, dirnames, filenames in os.walk(root_path, onerror=on_walk_error):
        # Prune ignored directories in-place (allow CI configuration dotdirs)
        dirnames[:] = [
            d
            for d in dirnames
            if d not in DEFAULT_IGNORED_DIRS
            and (not d.startswith(".") or d in (".github", ".circleci", ".gitlab", ".azure-pipelines"))
        ]

        for f in filenames:
            if is_lockfile(f) or is_minified(f):
                continue
            full_path = Path(dirpath) / f
            try:
                # Ensure it exists and is a regular file (not broken symlink, FIFO, or socket)
                if full_path.is_file():
                    yield full_path
            except OSError:
                continue
