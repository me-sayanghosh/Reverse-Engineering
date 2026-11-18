---
name: repo-reverse-engineer
description: Reverse engineer any GitHub repository or local codebase end to end, explain how the project works, document the codebase architecture, and produce structured reports including rebuild blueprints. Triggers on requests to reverse engineer this repo, explain how this GitHub project works, document this codebase, map the architecture of a repository, or how would I rebuild X.
---


## When to Use

- Understanding an unfamiliar codebase, repository, or library from scratch.
- Reverse engineering architecture, components, data models, APIs, and key execution flows.
- Producing a comprehensive codebase documentation report suite or architectural review.
- Planning a rewrite, clean-room reimplementation, or rebuild blueprint of an existing system.
- Auditing a repository for dependencies, operational configuration, secrets, and architectural risks.

## When NOT to Use

- Implementing a specific new feature or bug fix in an existing active workspace.
- Debugging a single runtime error or isolated stack trace.
- Running general repository maintenance or routine code formatting/linting tasks.
- Executing continuous deployment or infrastructure provisioning workflows.

## Inputs

The skill accepts the following parameters:

1. **`target`** (required): GitHub repository URL (HTTPS or SSH), shorthand `owner/repo`, or local filesystem path.
   - Default: Current workspace if no argument is provided.
2. **`ref`** (optional): Git branch, tag, or commit SHA to inspect.
   - Default: Repository default branch (`HEAD` / `main` / `master`).
3. **`subfolder`** (optional): Subdirectory path within a monorepo or large codebase to focus analysis on.
   - Default: Repository root (`/`).
4. **`mode`** (optional): Depth of reverse engineering execution (`quick`, `standard`, or `deep`).
   - Default: `standard`.
5. **`audience`** (optional): Target audience style for synthesis (`beginner` or `senior`).
   - Default: `senior`.

## Safety Rules

1. **Never execute untrusted repo code on host**: Default to static code analysis and parsing. Never run build scripts, test runners, install scripts, or hooks from an untrusted repository on the host machine.
2. **Never print secret values**: Only report secret names, environment variable keys, and file locations. Always redact tokens, passwords, and sensitive keys (e.g. mask as `AKIA****`).
3. **Respect software licenses**: Document the repository's license accurately and flag non-commercial or restrictive copyleft constraints.
4. **Require explicit user approval before sandbox execution**: If dynamic runtime analysis (Phase 4) is desired, run strictly in an isolated sandbox and obtain explicit user consent before starting containers or processes.

## Modes

| Mode | Target Scope & Depth | Phases Included | Outputs Generated |
| :--- | :--- | :--- | :--- |
| `quick` | High-level architectural overview & stack recon | Phases 0–2 | `00-SUMMARY.md`, `01-ARCHITECTURE.md` |
| `standard` | Full static reverse engineering of architecture, API, data model, and risks | Phases 0–3, 5–7 | Reports `00` through `07`, `09` |
| `deep` | Comprehensive reverse engineering plus runtime analysis & complete rebuild blueprint | All Phases (0–7) including Rebuild Blueprint | Complete suite: Reports `00` through `09` |

## Output Folder Convention

All reverse engineering artifacts and markdown reports are stored in:
`reverse-engineered/<repo-name>/`

The 10 report filenames are:
1. `00-SUMMARY.md` - Executive summary, purpose, high-level stack, and key findings.
2. `01-ARCHITECTURE.md` - System architecture, component topology, boundaries, and Mermaid diagrams.
3. `02-CODE-MAP.md` - Directory tree walkthrough, entrypoint rankings, and module catalog.
4. `03-API-AND-DATA.md` - Public API surface, HTTP/RPC/CLI routes, database schemas, and ER diagrams.
5. `04-FLOWS.md` - Critical path traces, sequence diagrams, and lifecycle state machines.
6. `05-DEPENDENCIES.md` - Internal and external dependency graph, licenses, and central hubs.
7. `06-CONFIG-AND-OPS.md` - Environment variables, configuration management, Docker/k8s/CI infrastructure.
8. `07-RISKS-AND-DEBT.md` - Technical debt, security risks, potential secret leaks, and architectural pitfalls.
9. `08-REBUILD-BLUEPRINT.md` - Clean-room reimplementation plan, phased milestones, prompts, and pseudocode.
10. `09-GLOSSARY-AND-QA.md` - Domain glossary, architecture decisions records (ADR) FAQ, and interrogation notes.

## No-Hallucination Rules

1. **Cite `file:line` for claims**: Every architectural, functional, or data model assertion must be backed by an exact file and line reference.
2. **Label `[inferred]` with confidence**: If a conclusion is inferred rather than directly observed in source code, mark it explicitly as `[inferred: high|medium|low]` and explain the deduction logic.
3. **Say "not found" instead of guessing**: If a pattern, test suite, configuration, or documentation file does not exist in the repository, explicitly state "not found" rather than inventing or assuming standard conventions.
4. **Prefer code over README**: When code and documentation disagree, treat actual source code implementation as the ground truth, and note the documentation discrepancy in `07-RISKS-AND-DEBT.md`.

## Citation Format Specification

Citations must reference repository files using exact line numbers or line ranges:
- Single line format: `path/to/file.ext:LINE` (e.g. `src/server.ts:42`)
- Multi-line range format: `path/to/file.ext:START-END` (e.g. `src/models/user.py:10-25`)

### Citation Examples

- **Valid citation example**: `src/auth/jwt.ts:45-58` references lines 45 through 58 in `src/auth/jwt.ts`.
- **Invalid citation example**: `User model file (around line 50)` is invalid because it lacks an exact relative file path and concrete line numbers.

## Script Index

The skill provides 8 dedicated automation scripts located in `scripts/`:

1. **`clone_repo.sh`**: Clones a remote repository or prepares a local path, capturing repository metadata and license.
   - Usage: `bash scripts/clone_repo.sh <url|path> [--branch X] [--subdir Y] [--out DIR] [--max-mb N] [--yes]`
2. **`repo_stats.py`**: Computes file counts, lines of code per language, directory tree structure, largest files, and monorepo hints.
   - Usage: `python3 scripts/repo_stats.py <root> [--json]`
3. **`detect_stack.py`**: Identifies languages, frameworks, package manifests, datastores, queues, and build/run commands.
   - Usage: `python3 scripts/detect_stack.py <root> [--json]`
4. **`find_entrypoints.py`**: Locates application bootstrap files, route roots, CLI commands, and worker entrypoints with citations.
   - Usage: `python3 scripts/find_entrypoints.py <root> [--json]`
5. **`dep_graph.py`**: Parses imports across languages, computes module-level dependencies, detects cycles, and generates Mermaid diagrams.
   - Usage: `python3 scripts/dep_graph.py <root> [--json] [--mermaid] [--depth N]`
6. **`extract_api_surface.py`**: Extracts HTTP endpoints, OpenAPI routes, GraphQL queries/mutations, gRPC services, and CLI commands.
   - Usage: `python3 scripts/extract_api_surface.py <root> [--json]`
7. **`extract_data_model.py`**: Analyzes database migrations, ORM models (Prisma, Mongoose, SQLAlchemy, Django), and generates Mermaid ERDs.
   - Usage: `python3 scripts/extract_data_model.py <root> [--json] [--mermaid]`
8. **`scan_secrets_env.py`**: Discovers environment variables, config keys, and flags potential secrets while strictly redacting values.
   - Usage: `python3 scripts/scan_secrets_env.py <root> [--json]`

## Phase 0: Intake & Safety

1. **Confirm Inputs & Modes**:
   - Determine target repository (`target`), branch/ref (`ref`), subfolder focus (`subfolder`), depth mode (`quick|standard|deep`), and target audience (`beginner|senior`).
2. **Execute Ingestion**:
   - Run the preparation script:
     ```bash
     bash scripts/clone_repo.sh "<target>" [--branch "<ref>"] [--subdir "<subfolder>"] [--out "reverse-engineered/<repo-name>"]
     ```
   - For remote repositories, this executes a shallow clone (`--depth 1`) with automated size pre-checks. For local workspaces, it inspects metadata in-place without copying.
3. **Inspect Captured Metadata**:
   - Read `reverse-engineered/<repo-name>/repo_meta.json` to extract exact commit SHA, active branch, and detected license.
   - Note license constraints in `00-SUMMARY.md` (e.g. AGPL/GPL copyleft or commercial suitability).
4. **Enforce Zero-Host-Execution Safety**:
   - Default strictly to static code inspection and script-based parsing.
   - Ask for explicit user confirmation before any containerized execution in Phase 4. Never execute untrusted scripts, hooks, or tests directly on the host machine.

## Phase 1: Recon & Orientation
TODO

## Phase 2: Architecture & Topology
TODO

## Phase 3: Deep Dives & Tracing
TODO

## Phase 4: Optional Runtime Observation
TODO

## Phase 5: Synthesis & Report Generation
TODO

## Phase 6: Verification & Cross-Checking
TODO

## Phase 7: Handoff & Next Steps
TODO

## Invocation Examples

1. **Remote GitHub Repository (Standard Mode)**:
   > "Reverse engineer this repository: https://github.com/expressjs/express and document how its middleware routing system works."
2. **Local Codebase Path**:
   > "Explain how this local project works: `/path/to/my-backend-repo`. Generate an architectural map and data model report."
3. **Monorepo Subfolder Focus**:
   > "Map the architecture of `https://github.com/trpc/trpc` focusing only on the `packages/server` subfolder."
4. **Deep Mode with Rebuild Blueprint**:
   > "Reverse engineer `https://github.com/fastify/fastify` in deep mode. I want a complete rebuild blueprint and implementation prompts to recreate it from scratch."
5. **Beginner Audience Orientation**:
   > "Explain how this GitHub project works for a junior developer: `https://github.com/pallets/flask`. Keep explanations accessible and provide an expanded glossary."

## References

Detailed guides, templates, and reference documentation:
- [Analysis Playbook](references/analysis-playbook.md): Ecosystem-specific investigation strategies across 10 stacks.
- [Output Templates](references/output-templates.md): Fill-in templates for reports 00 through 09.
- [Large Repository Strategy](references/large-repo-strategy.md): Sampling, ranking by import centrality, and disclosure of unanalyzed scope.
- [Mermaid Cheatsheet](references/mermaid-cheatsheet.md): Diagram syntax and examples for architecture, sequences, and ERDs.
