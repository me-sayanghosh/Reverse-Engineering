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
