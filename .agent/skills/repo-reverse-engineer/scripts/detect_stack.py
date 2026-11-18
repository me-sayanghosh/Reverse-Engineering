#!/usr/bin/env python3
"""Detect ecosystems, frameworks, databases, infrastructure, and commands in a repository."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common

MANIFEST_TO_ECOSYSTEM: dict[str, str] = {
    "package.json": "Node/TypeScript",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Pipfile": "Python",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "build.gradle.kts": "Kotlin/Gradle",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "pubspec.yaml": "Dart/Flutter",
    "Package.swift": "Swift",
    "mix.exs": "Elixir",
    ".csproj": ".NET/C#",
}


def detect_manifests(root_path: Path):
    """Detect package manifests and identify associated ecosystems."""
    root_path = Path(root_path).resolve()
    found_manifests = []
    ecosystems = set()

    for file_path in _common.walk_repo(root_path):
        name = file_path.name
        rel_path = str(file_path.relative_to(root_path))
        matched = False

        if name in MANIFEST_TO_ECOSYSTEM:
            eco = MANIFEST_TO_ECOSYSTEM[name]
            found_manifests.append({"path": rel_path, "manifest": name, "ecosystem": eco})
            ecosystems.add(eco)
            matched = True
        elif file_path.suffix == ".csproj":
            eco = MANIFEST_TO_ECOSYSTEM[".csproj"]
            found_manifests.append({"path": rel_path, "manifest": name, "ecosystem": eco})
            ecosystems.add(eco)
            matched = True

    return sorted(list(ecosystems)), found_manifests


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect repository technology stack, frameworks, databases, and build/run commands."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    ecosystems, manifests = detect_manifests(root_path)

    data = {
        "root": str(root_path),
        "ecosystems": ecosystems,
        "manifests": manifests,
        "frameworks": [],
        "datastores": [],
        "infra": [],
        "commands": {},
        "confidence": "high",
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Stack Detection for: {root_path}")


if __name__ == "__main__":
    main()
