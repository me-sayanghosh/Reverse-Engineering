# repo-reverse-engineer

An agentic skill for Google Antigravity that reverse engineers any GitHub repository or local codebase end-to-end. It produces an executive architectural breakdown, component models, data flow graphs, API surfaces, database entity-relationship models, and clean-room rebuild blueprints with line-numbered citations.

---

## 1. What It Does

`repo-reverse-engineer` performs automated, multi-phase static architectural reverse engineering on unfamiliar repositories:
- **Recon & Environment Discovery**: Automatically counts LOC by language, maps directory trees, detects 15+ package manifests, monorepos, frameworks, and datastores.
- **Entrypoint Identification**: Scans and ranks server bootstraps, HTTP listeners, CLI commands, queue workers, and web entrypoints.
- **Dependency & Centrality Graphing**: Parses import graphs (Python, JavaScript/TypeScript, Go, Rust, Java, C/C++, Swift, PHP), detects circular dependencies, and identifies architectural hub modules.
- **API & Data Surface Extraction**: Discovers REST routes, OpenAPI/Swagger specs, GraphQL schemas, gRPC protobufs, and database ORMs (Prisma, Mongoose, SQLAlchemy, Django, GORM, Diesel, SQL migrations).
- **Security & Secret Auditing**: Masks sensitive keys (`AKIA****`, `sk_live_****`), scans environment variables, and flags untrusted lifecycle hooks.
- **Clean-Room Rebuild Blueprints**: Produces phased rebuild blueprints with architectural pseudocode, deliverables, and ready-to-run prompts for coding agents.

---

## 2. Installation

You can install this skill either per-workspace or globally across all Antigravity projects.

### Option A: Workspace Installation (Project-Specific)
Install the skill into your project's `.agent/skills/` directory:
```bash
mkdir -p .agent/skills/
git clone https://github.com/your-org/repo-reverse-engineer.git .agent/skills/repo-reverse-engineer
```
Antigravity automatically discovers and activates skills located in `.agent/skills/`.

### Option B: Global Skills Installation (User Profile)
To make the skill available across all your repositories:
```bash
# macOS / Linux
mkdir -p ~/.gemini/antigravity/skills/
git clone https://github.com/your-org/repo-reverse-engineer.git ~/.gemini/antigravity/skills/repo-reverse-engineer

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$HOME\.gemini\antigravity\skills\"
git clone https://github.com/your-org/repo-reverse-engineer.git "$HOME\.gemini\antigravity\skills\repo-reverse-engineer"
```

---

## 3. Usage Examples

Invoke the skill through plain language instructions to Antigravity:

### High-Level Exploration
> "Reverse engineer this repository in quick mode and give me a summary of how it works."

### Standard Full-Suite Architectural Audit
> "Explain how `https://github.com/expressjs/morgan` works. Document the architecture, entrypoints, and data flow."

### Monorepo Subdirectory Focus
> "Reverse engineer `https://github.com/trpc/trpc` focusing only on the `packages/server` subfolder in standard mode."

### Clean-Room Rebuild Blueprint
> "Reverse engineer `https://github.com/fastify/fastify` in deep mode. I want a complete rebuild blueprint and implementation prompts to recreate it from scratch."

### Targeted for Junior Developers
> "Explain this codebase for a junior engineer: `https://github.com/pallets/flask` with audience set to beginner."

---

## 4. Modes

| Mode | Target Scope & Depth | Phases Included | Outputs Generated | Estimated Time |
| :--- | :--- | :--- | :--- | :--- |
| `quick` | High-level architectural overview & stack recon | Phases 0–2 | `00-SUMMARY.md`, `01-ARCHITECTURE.md` | 3–5 min |
| `standard` | Full static reverse engineering of architecture, API, data model, and risks | Phases 0–3, 5–7 | Reports `00` through `07`, `09` | 10–15 min |
| `deep` | Comprehensive reverse engineering plus runtime analysis & complete rebuild blueprint | All Phases (0–7) including Rebuild Blueprint | Complete suite: Reports `00` through `09` | 20–30 min |

All output reports are written to `./reverse-engineered/<repo-name>/`.

---

## 5. Safety Notes & Security Guarantees

1. **Zero Untrusted Code Execution**: The skill operates via strict static analysis and AST parsing. It **never** executes `npm install`, `pip install`, `make`, build hooks, or test runners from untrusted repositories on the host machine.
2. **Mandatory Secret Redaction**: Found credentials, API keys, and tokens are recursively masked (e.g. `AKIA****`, `sk_live_****`). Raw secret values are never printed to logs or markdown reports.
3. **Lifecycle Hook Auditing**: High-risk lifecycle hooks (such as `postinstall` or `preinstall` scripts containing `curl` or `wget`) are flagged in `07-RISKS-AND-DEBT.md` without running them.
4. **License Awareness**: The repository license (MIT, Apache, GPL, MPL, etc.) is detected from source and noted with copyleft or commercial usage constraints.

---

## 6. Limitations & Platform Notes

- **Dynamic Metaprogramming**: Heavily dynamic runtime metaprogramming (e.g. Ruby `eval`, Python `getattr` hacks) may not resolve completely via static AST inspection and will be cataloged with file citations for manual review.
- **Large Repository Strategy**: For codebases exceeding 50,000 lines of code, the skill prioritizes top hub modules using import centrality and explicitly records unanalyzed subsystems in a "Scope & Not Analyzed Disclosure" section.
- **Cross-Platform Compatibility**:
  - **macOS & Linux**: Native support across Python 3.10+ and Bash 3.2+.
  - **Windows**: All Python analysis scripts (`*.py`) are fully cross-platform and use standard library `pathlib.Path`. When executing on Windows without WSL or Git Bash, `clone_repo.sh` can be substituted with native `git clone --depth 1` into the target directory.
