# Contributing to repo-reverse-engineer

Thank you for helping improve the `repo-reverse-engineer` skill.

## How to Add a New Ecosystem Parser

To support an additional programming language or framework ecosystem, follow these steps:

### 1. Update Ecosystem Detection (`scripts/detect_stack.py`)
- Add your ecosystem name to the detection heuristics if not present.
- Register new package manifest files in `MANIFEST_TO_ECOSYSTEM` (for example, `pubspec.yaml`, `build.gradle`, or `mix.exs`).
- Add framework identification tokens in `NODE_PKG_TO_FRAMEWORK`, `PYTHON_PKG_TO_FRAMEWORK`, or `OTHER_FRAMEWORKS_MAP`.
- Extend `detect_datastores_and_queues` if the ecosystem uses dedicated configuration formats.

### 2. Update File Extension Mapping (`scripts/_common.py`)
- Add language extensions to `EXT_TO_LANG` in `scripts/_common.py`.

### 3. Implement Dependency Graph Parsing (`scripts/dep_graph.py`)
- Add an AST or regex parser for your language's import and require statements.
- Distinguish between standard library imports, third-party packages, and relative internal module paths.

### 4. Implement Route & API Extraction (`scripts/extract_api_surface.py`)
- Add routing regex patterns for popular web frameworks in that ecosystem.
- Tag routes with authentication indicators if known middleware decorators are present.

### 5. Add Unit & Regression Tests
- Create a test file in `tests/test_<ecosystem>.py` or extend existing test suites.
- Verify everything runs cleanly by running:
  ```bash
  bash tests/run_tests.sh
  ```

## Code Quality Guidelines
- Zero external Python dependencies: use only Python standard library.
- Fast execution: avoid deep recursive directory scans when targeted manifests suffice.
- Security first: never execute target repository code during analysis.
