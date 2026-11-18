# Large Repository Reverse Engineering Strategy

When analyzing codebases exceeding 50,000 lines of code or complex monorepos containing dozens of packages, reading every source file line by line is inefficient and exceeds token limits. This document defines the prioritization, sampling methodology, and disclosure rules for large repositories.

## Prioritization & Sampling Procedure

1. **Reconnaissance & Structural Indexing**:
   - Run `repo_stats.py` to establish the total LOC, directory depth, and detect if monorepo workspace configurations exist.
   - Run `detect_stack.py` to map all package manifests and active ecosystems.

2. **Rank Files by Significance**:
   - Compute import centrality using `dep_graph.py` (files with highest in-degree / hub modules).
   - Locate entrypoint proximities using `find_entrypoints.py` (server listeners, CLI roots, main procedures).
   - Identify top 15 largest source files from `repo_stats.py`.
   - Identify highest churn files from git commit logs.

3. **Tiered Reading Strategy**:
   - **Tier 1 (Deep Analysis - 100% Read)**: Entrypoints, public API route handlers, database schema files, core configuration files, and top 10 central modules.
   - **Tier 2 (Structural Skim - Signature & Types Read)**: Service classes, helper modules, middleware, interface declarations. Read signatures, public methods, and docstrings.
   - **Tier 3 (Cataloged Only)**: Test fixtures, mock data, generated clients, CSS/styling, legacy migration histories.

4. **Monorepo Package Isolation**:
   - Split analysis on package boundaries (e.g., `packages/*` or `apps/*`).
   - Analyze shared core packages (`@app/core`, `common/`) first.
   - Map inter-package dependency edges before deep-diving into individual leaf applications.

## What to Report as "Not Analyzed"

In large repositories, intellectual honesty and avoiding false confidence is paramount. Every report suite on a sampled or large repository must include an explicit **"Scope & Not Analyzed Disclosure"** section listing:
1. **Directories / Subsystems Excluded**: Specific folders skipped due to depth or scope (e.g. `legacy/`, `e2e/`, `benchmarks/`).
2. **Untracked Code Paths**: Edge cases or fallback plugins not verified against running instances.
3. **External Services Mocked**: Third-party integrations whose exact remote behavior is assumed from client types.
4. **Sampling Rationale**: The specific mathematical ranking threshold used (e.g., "Analyzed top 30 central files representing 68% of dependency paths").
