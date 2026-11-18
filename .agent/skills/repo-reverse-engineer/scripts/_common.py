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
}

LOCKFILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Gemfile.lock",
    "go.sum",
    "flake.lock",
    "bun.lockb",
}


def is_too_large(path: str | Path, limit_bytes: int = 1024 * 1024) -> bool:
    """Return True if file size exceeds limit_bytes (default 1MB)."""
    try:
        return os.path.getsize(path) > limit_bytes
    except OSError:
        return True


def is_binary(path: str | Path) -> bool:
    """Return True if file appears to be binary based on null bytes or decoding."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
            # Try decoding as utf-8
            chunk.decode("utf-8")
            return False
    except (UnicodeDecodeError, OSError):
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
}


def is_lockfile(filename: str) -> bool:
    return filename in LOCKFILES


def is_minified(filename: str) -> bool:
    lower = filename.lower()
    return (
        lower.endswith(".min.js")
        or lower.endswith(".min.css")
        or lower.endswith(".bundle.js")
        or lower.endswith(".bundle.css")
        or lower.endswith(".map")
    )


def die(message: str, code: int = 1) -> None:
    """Print error message to stderr and exit with non-zero code."""
    sys.stderr.write(f"ERROR: {message}\n")
    sys.exit(code)


def output_json(data: Any) -> None:
    """Format and print data as indented JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def walk_repo(root: str | Path) -> Generator[Path, None, None]:
    """Walk repository root directory, yielding Path objects for non-ignored files."""
    root_path = Path(root).resolve()
    if not root_path.exists():
        die(f"Path does not exist: {root_path}")
    if root_path.is_file():
        yield root_path
        return

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".")]

        for f in filenames:
            if is_lockfile(f) or is_minified(f):
                continue
            full_path = Path(dirpath) / f
            yield full_path
