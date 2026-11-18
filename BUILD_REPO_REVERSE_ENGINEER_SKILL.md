# Build Prompt: `repo-reverse-engineer` Antigravity Skill (130 micro-steps)

## Your role
You are building a reusable Antigravity Skill named `repo-reverse-engineer`. Given any GitHub repo (URL or local path), the skill makes an agent reverse engineer it end to end and produce a report set: architecture, code map, API and data model, flows, dependencies, config/ops, risks, and a rebuild blueprint.

## Working rules (follow strictly)
1. Work on **ONE step at a time**, in order. Never batch steps.
2. Every step has a **Do** and a **Verify**. After doing the step, run the Verify check yourself and print `STEP N: PASS` or `STEP N: FAIL (reason)`.
3. If a step FAILS, fix it and re-verify. Do not move on until it PASSES.
4. Maintain `.agent/skills/repo-reverse-engineer/BUILD_PROGRESS.md` as a checklist. Tick each step only after PASS. Delete this file in Step 129.
5. Keep scripts dependency-light (Python stdlib / bash where possible), cross-platform, with `--help`, clear errors and non-zero exit codes on failure.
6. Never execute untrusted repo code on the host. Static analysis by default.
7. Never print secret values, only names and locations.
8. Every script must output machine-readable JSON (`--json`) as well as human-readable text.
9. If something is ambiguous, pick the simplest reasonable option, note it in `BUILD_PROGRESS.md`, and continue.

Target root: `.agent/skills/repo-reverse-engineer/` (call it `$SKILL`).

---

## PHASE A: Setup (Steps 1–8)

**Step 1 – Create root folder**
- Do: create `$SKILL/`.
- Verify: `ls $SKILL` succeeds.

**Step 2 – Create subfolders**
- Do: create `scripts/`, `references/`, `examples/sample-output/`, `tests/`.
- Verify: list the tree; all four exist.

**Step 3 – Create progress file**
- Do: create `BUILD_PROGRESS.md` with a checkbox list of all 130 step titles.
- Verify: file has 130 checkbox lines.

**Step 4 – Check runtime tools**
- Do: detect `python3 --version`, `git --version`, `bash --version`, `node --version` (optional).
- Verify: python3 ≥ 3.9 and git present; record versions in `BUILD_PROGRESS.md`.

**Step 5 – Create a shared helper module**
- Do: create `scripts/_common.py` with: JSON output helper, error/exit helper, path-ignore list (node_modules, .git, dist, build, vendor, target, __pycache__, .venv, lockfiles, minified files), and a `walk_repo(root)` generator that respects the ignore list.
- Verify: `python3 -c "import sys; sys.path.insert(0,'scripts'); import _common"` runs with no error.

**Step 6 – Add binary/large-file guard**
- Do: in `_common.py`, add `is_binary(path)` and `is_too_large(path, limit=1MB)`.
- Verify: unit-test both with a temp text file and a temp binary file.

**Step 7 – Add language-by-extension map**
- Do: in `_common.py`, add `EXT_TO_LANG` covering at least 40 common extensions.
- Verify: assert `.py→Python`, `.ts→TypeScript`, `.go→Go`, `.rs→Rust`, `.java→Java`.

**Step 8 – Add a tiny test runner**
- Do: create `tests/run_tests.sh` that runs all `tests/test_*.py` and prints a summary.
- Verify: running it with zero tests exits 0 and prints "0 tests".

---

## PHASE B: SKILL.md skeleton (Steps 9–20)

**Step 9 – Write frontmatter**
- Do: create `SKILL.md` with YAML frontmatter: `name: repo-reverse-engineer` and a `description` that clearly triggers on "reverse engineer this repo", "explain how this GitHub project works", "document this codebase", "map the architecture of <url>", "how would I rebuild X".
- Verify: frontmatter parses as valid YAML (use python yaml or a manual check); description is 1–3 sentences.

**Step 10 – Add "When to use / not use" section**
- Do: list triggers and non-triggers (e.g. not for writing new features, not for debugging a single bug).
- Verify: both lists have ≥ 4 bullets.

**Step 11 – Add inputs section**
- Do: document inputs: repo URL or path, optional branch/tag/commit, optional subfolder, mode (`quick|standard|deep`), optional audience (`beginner|senior`).
- Verify: all five inputs appear with defaults.

**Step 12 – Add safety rules block**
- Do: write the safety rules (no executing untrusted code, no printing secrets, respect licenses, ask before sandbox execution).
- Verify: grep SKILL.md for "never execute" and "secret" both present.

**Step 13 – Add modes table**
- Do: table of modes: quick (~overview, phases 0–2), standard (phases 0–3 + 5–7), deep (all phases + rebuild blueprint).
- Verify: table has 3 rows and lists which phases each includes.

**Step 14 – Add output folder convention**
- Do: define output at `reverse-engineered/<repo-name>/` with the 10 report filenames (00–09).
- Verify: all 10 filenames listed exactly.

**Step 15 – Add "no hallucination" rules**
- Do: rules: cite `file:line` for claims, label `[inferred]` with confidence, say "not found" instead of guessing, prefer code over README.
- Verify: all four rules present.

**Step 16 – Add citation format spec**
- Do: define citation format `path/to/file.ext:LINE` or `:START-END`.
- Verify: includes one valid and one invalid example.

**Step 17 – Add script index**
- Do: list each planned script with a one-line purpose and CLI usage placeholder.
- Verify: 8 scripts listed (clone_repo, repo_stats, detect_stack, find_entrypoints, dep_graph, extract_api_surface, extract_data_model, scan_secrets_env).

**Step 18 – Add placeholders for phases 0–7**
- Do: add headings "Phase 0" through "Phase 7" with `TODO` bodies.
- Verify: 8 phase headings exist.

**Step 19 – Add invocation examples**
- Do: add 5 sample user prompts covering URL, local path, monorepo subfolder, deep mode, beginner audience.
- Verify: 5 examples present.

**Step 20 – Lint SKILL.md structure**
- Do: write `tests/test_skill_md.py` checking frontmatter, required headings and phase count.
- Verify: test passes.

---

## PHASE C1: `clone_repo.sh` (Steps 21–28)

**Step 21 – Create script skeleton**
- Do: `scripts/clone_repo.sh` with usage, `set -euo pipefail`, args: `<url|path> [--branch X] [--subdir Y] [--out DIR] [--max-mb N] [--yes]`.
- Verify: `bash scripts/clone_repo.sh --help` prints usage, exit 0.

**Step 22 – Parse and validate input**
- Do: accept GitHub HTTPS/SSH URLs, `owner/repo` shorthand, or a local path; reject anything else.
- Verify: test 4 inputs (valid URL, shorthand, local dir, garbage), garbage exits non-zero.

**Step 23 – Local path mode**
- Do: if input is a local dir, skip cloning and just copy/symlink metadata.
- Verify: run on `$SKILL` itself; it reports the path without network use.

**Step 24 – Size pre-check**
- Do: for GitHub repos, query the GitHub API for repo size (unauthenticated); if > `--max-mb` (default 500) and no `--yes`, stop and print a confirmation message.
- Verify: simulate with a tiny `--max-mb 1` on a known repo; it stops with a clear message.

**Step 25 – Shallow clone**
- Do: `git clone --depth 1` (+ `--branch` if given) into the output dir; support `--subdir` via sparse-checkout.
- Verify: clone a small public repo; `.git` exists, depth is 1.

**Step 26 – Metadata capture**
- Do: write `repo_meta.json` with URL, commit SHA, branch, clone date, license file detected, default branch.
- Verify: JSON valid and contains all 6 keys.

**Step 27 – License detection**
- Do: find `LICENSE*`/`COPYING*`; guess SPDX id from first lines (MIT, Apache-2.0, GPL, BSD, none).
- Verify: test on a repo with MIT license returns "MIT".

**Step 28 – Error handling**
- Do: handle network failure, private repo (auth required), missing branch with specific messages.
- Verify: trigger each error and confirm a distinct message and non-zero exit.

---

## PHASE C2: `repo_stats.py` (Steps 29–36)

**Step 29 – Skeleton**
- Do: `scripts/repo_stats.py <root> [--json]` using `_common`.
- Verify: `--help` works.

**Step 30 – File counts & LOC by language**
- Do: count files and non-blank lines per language.
- Verify: on this skill folder, Python and Markdown appear with plausible counts.

**Step 31 – Tree summary**
- Do: print directory tree to depth 3 with file counts per dir.
- Verify: output depth ≤ 3 and top-level dirs match `ls`.

**Step 32 – Largest files**
- Do: list top 15 largest source files by lines.
- Verify: sorted descending; ignores lockfiles/minified.

**Step 33 – Churn & age hints**
- Do: if `.git` has history, list 10 most recently modified files; otherwise skip gracefully.
- Verify: no crash on shallow clone.

**Step 34 – Test/doc/CI presence**
- Do: detect tests dirs, docs dirs, CI configs (`.github/workflows`, `.gitlab-ci.yml`, etc.).
- Verify: returns booleans plus paths.

**Step 35 – Monorepo hint**
- Do: flag monorepo if multiple manifests exist in subfolders or workspaces config (npm/pnpm/yarn workspaces, Cargo workspace, go.work, Lerna, Nx, Turborepo).
- Verify: test with a fake folder containing 2 `package.json` files.

**Step 36 – JSON schema & test**
- Do: finalize JSON shape; write `tests/test_repo_stats.py` using a temp fixture repo.
- Verify: test passes.

---

## PHASE C3: `detect_stack.py` (Steps 37–45)

**Step 37 – Skeleton**
- Do: `scripts/detect_stack.py <root> [--json]`.
- Verify: `--help` works.

**Step 38 – Manifest detection table**
- Do: map manifest files to ecosystems: package.json, pyproject.toml, requirements.txt, Pipfile, go.mod, Cargo.toml, pom.xml, build.gradle(.kts), Gemfile, composer.json, *.csproj, pubspec.yaml, Package.swift, mix.exs.
- Verify: table has ≥ 14 entries; unit test finds each from a fixture.

**Step 39 – Node/TS framework detection**
- Do: parse package.json deps for React, Next, Vue, Nuxt, Svelte, Angular, Express, Fastify, NestJS, Koa, Hono, Prisma, Mongoose, Socket.IO, Vite, Webpack, Jest, Vitest.
- Verify: fixture package.json produces matching tags.

**Step 40 – Python framework detection**
- Do: parse requirements/pyproject for Django, Flask, FastAPI, SQLAlchemy, Celery, Pydantic, PyTorch, TensorFlow, pytest.
- Verify: fixture produces matching tags.

**Step 41 – Go/Rust/Java/others**
- Do: detect Gin, Echo, Fiber, gRPC (Go); Actix, Axum, Tokio, Rocket (Rust); Spring Boot, Quarkus, Micronaut (Java/Kotlin); Rails, Sinatra (Ruby); Laravel (PHP); ASP.NET (C#).
- Verify: one fixture per ecosystem passes.

**Step 42 – Infra detection**
- Do: detect Dockerfile, docker-compose, Kubernetes manifests, Terraform, Helm, Serverless, Vercel/Netlify configs.
- Verify: fixture with a Dockerfile and a `.tf` file is detected.

**Step 43 – Database/queue detection**
- Do: detect Postgres, MySQL, MongoDB, Redis, SQLite, Kafka, RabbitMQ, SQS from deps and config files.
- Verify: fixture with `redis` and `pg` deps is detected.

**Step 44 – Build/test/run command inference**
- Do: infer install/build/test/start commands from scripts sections, Makefile targets, README code blocks.
- Verify: fixture package.json scripts map to commands.

**Step 45 – Output & test**
- Do: JSON with `ecosystems`, `frameworks`, `datastores`, `infra`, `commands`, `confidence`; write `tests/test_detect_stack.py`.
- Verify: test passes.

---

## PHASE C4: `find_entrypoints.py` (Steps 46–54)

**Step 46 – Skeleton**
- Do: `scripts/find_entrypoints.py <root> [--json]`.
- Verify: `--help` works.

**Step 47 – Manifest-declared entrypoints**
- Do: read `main`/`bin`/`scripts.start` (npm), `[project.scripts]`/`__main__.py` (Python), `cmd/*/main.go` (Go), `src/main.rs`/`src/bin` (Rust), `Main` classes (Java).
- Verify: fixture for each ecosystem yields entries.

**Step 48 – Server bootstrap patterns**
- Do: regex-detect `app.listen`, `createServer`, `uvicorn.run`, `app.run`, `http.ListenAndServe`, `@SpringBootApplication`.
- Verify: fixture lines detected with line numbers.

**Step 49 – Route definition patterns**
- Do: detect Express/Fastify/Flask/FastAPI/Gin/Spring/Rails route declarations and count them per file.
- Verify: fixture files with 3 routes report 3.

**Step 50 – CLI & worker detection**
- Do: detect argparse/click/typer/commander/yargs/cobra/clap usage; queue workers (Celery, Bull, Sidekiq); cron schedules.
- Verify: fixtures detected.

**Step 51 – Frontend entrypoints**
- Do: detect `index.html`, `main.tsx/jsx`, `App.*`, Next `app/` or `pages/`, Vite config.
- Verify: fixture Next-style tree is detected.

**Step 52 – Ranking**
- Do: rank entrypoints by confidence (manifest-declared > bootstrap pattern > filename heuristic).
- Verify: output sorted; each has `reason`.

**Step 53 – Line-numbered evidence**
- Do: every result includes `file:line` evidence.
- Verify: random 3 results open to the right line.

**Step 54 – Test**
- Do: write `tests/test_find_entrypoints.py` with a multi-language fixture.
- Verify: test passes.

---

## PHASE C5: `dep_graph.py` (Steps 55–63)

**Step 55 – Skeleton**
- Do: `scripts/dep_graph.py <root> [--json] [--mermaid] [--depth N]`.
- Verify: `--help` works.

**Step 56 – JS/TS import parser**
- Do: regex parse `import ... from`, `require()`, dynamic `import()`; resolve relative paths to files.
- Verify: fixture A→B→C chain produces 2 edges.

**Step 57 – Python import parser**
- Do: use `ast` to parse imports; resolve relative and package-internal imports.
- Verify: fixture package produces expected edges.

**Step 58 – Go/Rust/Java import parsers**
- Do: basic parsers for `import "module/path"`, `use crate::`, `import com.x.y`; resolve to internal modules only.
- Verify: one fixture each.

**Step 59 – Internal vs external split**
- Do: classify each import as internal / stdlib / external-package.
- Verify: fixture shows all three types.

**Step 60 – Module-level aggregation**
- Do: collapse file-level edges to directory/package-level for readability.
- Verify: 20-file fixture collapses to ≤ 6 nodes.

**Step 61 – Centrality & cycles**
- Do: compute in-degree/out-degree, flag top 10 central modules and detect circular dependencies.
- Verify: fixture with a deliberate cycle flags it.

**Step 62 – Mermaid output**
- Do: emit `graph LR` Mermaid limited to 40 nodes (aggregate the rest into "other").
- Verify: output starts with `graph LR` and node count ≤ 40.

**Step 63 – Test**
- Do: write `tests/test_dep_graph.py`.
- Verify: test passes.

---

## PHASE C6: `extract_api_surface.py` (Steps 64–71)

**Step 64 – Skeleton**
- Do: `scripts/extract_api_surface.py <root> [--json]`.
- Verify: `--help` works.

**Step 65 – HTTP routes (Node)**
- Do: extract method + path + handler file:line from Express/Fastify/Koa/Hono/Nest decorators.
- Verify: fixture with 4 routes returns 4 entries.

**Step 66 – HTTP routes (Python/Go/Java/Ruby)**
- Do: Flask/FastAPI/Django urls, Gin/Echo/chi, Spring mappings, Rails `routes.rb`.
- Verify: one fixture per framework.

**Step 67 – OpenAPI/Swagger ingestion**
- Do: if `openapi.*`/`swagger.*` exists, parse paths and methods.
- Verify: fixture spec yields expected count.

**Step 68 – GraphQL / gRPC / tRPC**
- Do: parse `.graphql` schemas, `.proto` services, tRPC routers.
- Verify: fixtures detected.

**Step 69 – CLI commands & public exports**
- Do: collect CLI subcommands and library public exports (`__all__`, `export` from index files).
- Verify: fixture yields entries.

**Step 70 – Auth hints**
- Do: tag routes near auth middleware (`authenticate`, `requireAuth`, `@UseGuards`, `login_required`).
- Verify: fixture tags protected routes.

**Step 71 – Test**
- Do: write `tests/test_extract_api_surface.py`.
- Verify: test passes.

---

## PHASE C7: `extract_data_model.py` (Steps 72–79)

**Step 72 – Skeleton**
- Do: `scripts/extract_data_model.py <root> [--json] [--mermaid]`.
- Verify: `--help` works.

**Step 73 – SQL/migration parser**
- Do: parse `CREATE TABLE` statements and migration files into tables/columns/FKs.
- Verify: fixture with 3 tables and 2 FKs parses correctly.

**Step 74 – Prisma / Sequelize / TypeORM**
- Do: parse `schema.prisma` models and relations; detect decorator-based entities.
- Verify: fixture schema yields models and relations.

**Step 75 – Mongoose / MongoDB schemas**
- Do: parse `new Schema({...})` fields and `ref` relations.
- Verify: fixture yields fields.

**Step 76 – Python ORMs**
- Do: SQLAlchemy models, Django models, Pydantic models (fields and FKs).
- Verify: fixture yields fields.

**Step 77 – Go/Java/Rust types**
- Do: GORM structs, JPA `@Entity`, Diesel/SeaORM basics.
- Verify: one fixture each.

**Step 78 – Mermaid ERD output**
- Do: emit `erDiagram` capped at 25 entities.
- Verify: output starts with `erDiagram`; relationships render syntactically.

**Step 79 – Test**
- Do: write `tests/test_extract_data_model.py`.
- Verify: test passes.

---

## PHASE C8: `scan_secrets_env.py` (Steps 80–86)

**Step 80 – Skeleton**
- Do: `scripts/scan_secrets_env.py <root> [--json]`.
- Verify: `--help` works.

**Step 81 – Env var usage discovery**
- Do: find `process.env.X`, `os.environ["X"]`, `os.getenv`, `System.getenv`, `os.Getenv`, `.env.example` keys. Output names only.
- Verify: fixture lists names, never values.

**Step 82 – Config file keys**
- Do: list keys from `config.*`, `application.yml`, `settings.py` constants (names only).
- Verify: fixture passes.

**Step 83 – Secret pattern detection**
- Do: detect AWS keys, GitHub tokens, private key headers, Slack/Stripe keys, high-entropy strings in committed files. Mask results as `AKIA****`.
- Verify: fixture with fake secrets is flagged and the output contains no full secret.

**Step 84 – Redaction guarantee**
- Do: add a final output filter that masks anything matching secret patterns.
- Verify: grep output for the fake secret's middle characters; zero matches.

**Step 85 – Categorize env vars**
- Do: tag env vars as db/auth/third-party/feature-flag/infra by name heuristics.
- Verify: `DATABASE_URL→db`, `JWT_SECRET→auth`.

**Step 86 – Test**
- Do: write `tests/test_scan_secrets_env.py`.
- Verify: test passes.

---

## PHASE D: References (Steps 87–94)

**Step 87 – `analysis-playbook.md` skeleton**
- Do: create with sections per ecosystem: Node/TS, Python, Go, Rust, Java/Kotlin, .NET, Ruby, PHP, mobile, ML/data repos.
- Verify: 10 section headings.

**Step 88 – Fill Node/TS and Python sections**
- Do: for each, list where to look first (entrypoints, routing, state, DB layer, config), common patterns, common pitfalls.
- Verify: each section ≥ 8 bullets.

**Step 89 – Fill remaining ecosystems**
- Do: same for Go, Rust, Java/Kotlin, .NET, Ruby, PHP, mobile, ML.
- Verify: each section ≥ 5 bullets.

**Step 90 – `output-templates.md` for reports 00–04**
- Do: write fill-in templates for SUMMARY, ARCHITECTURE, CODE-MAP, API-AND-DATA, FLOWS.
- Verify: each template has headings and placeholder markers like `{{...}}`.

**Step 91 – Templates for reports 05–09**
- Do: DEPENDENCIES, CONFIG-AND-OPS, RISKS-AND-DEBT, REBUILD-BLUEPRINT, GLOSSARY-AND-QA.
- Verify: all 10 templates present.

**Step 92 – `large-repo-strategy.md`**
- Do: document sampling strategy: rank by import centrality, size, churn and entrypoint proximity; read top-N fully; skim rest; split work per package.
- Verify: includes a numbered procedure and a "what to report as not analyzed" section.

**Step 93 – `mermaid-cheatsheet.md`**
- Do: short reference for flowchart, sequenceDiagram, erDiagram, classDiagram syntax, plus common mistakes.
- Verify: one valid example of each diagram type.

**Step 94 – Reference link check**
- Do: ensure SKILL.md links to all four references with relative paths.
- Verify: a script confirms each linked file exists.

---

## PHASE E: SKILL.md workflow content (Steps 95–106)

**Step 95 – Phase 0 body (Intake & safety)**
- Do: write exact steps: confirm inputs, run `clone_repo.sh`, read `repo_meta.json`, note license, ask before any execution.
- Verify: references `clone_repo.sh` and `repo_meta.json`.

**Step 96 – Phase 1 body (Recon)**
- Do: run `repo_stats`, `detect_stack`, `find_entrypoints`; read README/CONTRIBUTING/docs/CI/Dockerfile; write what/who/stack/how-to-run.
- Verify: references all three scripts plus the readme-reading step.

**Step 97 – Phase 2 body (Architecture mapping)**
- Do: run `dep_graph`; identify layers and boundaries; produce component diagram; monorepo handling.
- Verify: mentions Mermaid and monorepo.

**Step 98 – Phase 3 body (Deep dives)**
- Do: prioritized list: API, data model, auth, state, config, integrations, jobs, caching, errors, logging, tests, security; trace 3–5 flows as sequence diagrams.
- Verify: all 12 topics plus "3–5 flows" present.

**Step 99 – Phase 4 body (Optional runtime)**
- Do: sandbox-only execution, user approval required, compare observed behavior with static findings.
- Verify: contains the words "approval" and "sandbox".

**Step 100 – Phase 5 body (Synthesis)**
- Do: map each report file to its template and the scripts feeding it; cap each at ~400 lines.
- Verify: 10 report files mapped.

**Step 101 – Phase 6 body (Verification pass)**
- Do: checklist: citations present, `[inferred]` labels, diagrams re-checked, "not analyzed" list.
- Verify: 4 checklist items.

**Step 102 – Phase 7 body (Handoff)**
- Do: summary format: report path, top 5 things to know, follow-up offers.
- Verify: all three elements present.

**Step 103 – Audience flag behavior**
- Do: define how `beginner` vs `senior` changes tone, depth and glossary size.
- Verify: both variants described.

**Step 104 – Failure & fallback section**
- Do: what to do when clone fails, repo is private, language unsupported by scripts (fall back to manual grep/reading), or repo is huge.
- Verify: 4 scenarios covered.

**Step 105 – Parallelization guidance**
- Do: instruct using subagents/parallel workers per package or per deep-dive topic when available; merge into a single report set.
- Verify: guidance present.

**Step 106 – Re-run SKILL.md lint**
- Do: update `tests/test_skill_md.py` for the filled content (no remaining `TODO`).
- Verify: test passes and zero `TODO` strings remain.

---

## PHASE F: Example output (Steps 107–110)

**Step 107 – Create a tiny demo repo**
- Do: in `tests/fixtures/demo-app/` create a small Express + MongoDB-style app (≈ 8 files) with routes, a model, auth middleware, `.env.example`.
- Verify: the folder has ≥ 8 files and a package.json.

**Step 108 – Run all scripts on the demo**
- Do: run all 8 scripts with `--json`, save outputs under `tests/fixtures/demo-output/`.
- Verify: 8 JSON files, all valid JSON.

**Step 109 – Hand-write sample reports**
- Do: write `examples/sample-output/` with `00-SUMMARY.md`, `01-ARCHITECTURE.md`, `03-API-AND-DATA.md` for the demo app using the templates, with real `file:line` citations.
- Verify: every citation resolves to an existing file and line in the demo repo (write a quick checker).

**Step 110 – Sample rebuild blueprint**
- Do: add `examples/sample-output/08-REBUILD-BLUEPRINT.md` for the demo (milestones, pseudocode, per-milestone prompts).
- Verify: ≥ 4 milestones, each with a prompt.

---

## PHASE G: Real-world testing (Steps 111–122)

**Step 111 – Pick test repos**
- Do: choose 3 public repos: (a) small single-language CLI, (b) full-stack web app, (c) monorepo. Record their URLs in `tests/REAL_REPOS.md`.
- Verify: 3 URLs listed.

**Step 112 – Test repo A: clone**
- Do: run `clone_repo.sh` on repo A.
- Verify: `repo_meta.json` valid, commit SHA present.

**Step 113 – Test repo A: scripts**
- Do: run the 8 scripts on repo A.
- Verify: no crashes; each output non-empty or explicitly "none found".

**Step 114 – Test repo A: full workflow**
- Do: follow SKILL.md phases 0–7 in `standard` mode and write the report set.
- Verify: all expected report files exist and each claim has a citation.

**Step 115 – Test repo B: clone + scripts**
- Do: same as 112–113 for the full-stack app.
- Verify: API surface and data model outputs non-empty.

**Step 116 – Test repo B: full workflow (deep)**
- Do: run `deep` mode including the rebuild blueprint.
- Verify: `08-REBUILD-BLUEPRINT.md` exists and its milestones map to real modules.

**Step 117 – Test repo C: monorepo**
- Do: run recon and confirm monorepo detection and per-package mapping.
- Verify: report lists each package with its role.

**Step 118 – Spot-check accuracy**
- Do: for each test repo, randomly sample 10 claims from the reports and check them against the code.
- Verify: ≥ 90% correct; log errors in `tests/ACCURACY_LOG.md`.

**Step 119 – Fix script bugs found**
- Do: fix every crash/mis-parse discovered; add a regression test per fix.
- Verify: `tests/run_tests.sh` all pass.

**Step 120 – Fix workflow gaps**
- Do: update SKILL.md and references where the agent got confused or skipped steps.
- Verify: re-run one test repo in `quick` mode; the agent follows the workflow without help.

**Step 121 – Safety test**
- Do: test on a fixture repo containing a malicious-looking `postinstall` script and a fake secret.
- Verify: the skill does NOT execute it, flags it in RISKS, and masks the secret.

**Step 122 – Large-repo test**
- Do: run on a repo > 50k LOC (or simulate) and confirm the large-repo strategy kicks in and "not analyzed" list is produced.
- Verify: the report includes sampling rationale and a not-analyzed section.

---

## PHASE H: Polish & packaging (Steps 123–130)

**Step 123 – Script permissions & shebangs**
- Do: add shebangs, `chmod +x` all scripts.
- Verify: `ls -l scripts/` shows executable bits.

**Step 124 – Cross-platform check**
- Do: scan scripts for hard-coded POSIX-only paths; add Windows notes (or Python fallbacks) in README.
- Verify: no hard-coded `/tmp` or `/home`.

**Step 125 – Write `README.md`**
- Do: for sharing: what it does, install (workspace vs global skills folder), usage examples, modes, safety notes, limitations.
- Verify: all 6 sections present.

**Step 126 – Add `LICENSE` and `CONTRIBUTING.md`**
- Do: MIT license placeholder and a short contribution guide (how to add an ecosystem parser).
- Verify: both files exist.

**Step 127 – Token/size audit**
- Do: check SKILL.md length; move any long content into `references/` so SKILL.md stays focused (aim < 500 lines).
- Verify: `wc -l SKILL.md` under 500.

**Step 128 – Final full test run**
- Do: run `tests/run_tests.sh`.
- Verify: 0 failures.

**Step 129 – Clean up**
- Do: delete `BUILD_PROGRESS.md`, temp clones, `__pycache__`.
- Verify: tree contains only intended files.

**Step 130 – Final report to me**
- Do: print the final tree, a table of test results (repos tested, pass/fail, accuracy %), known limitations, and install instructions (workspace path and global path).
- Verify: report includes all four items. Then stop and wait for my feedback.

---

## Definition of done
- All 130 steps show PASS.
- `tests/run_tests.sh` passes with 0 failures.
- The skill produces a complete, cited report set on 3 different real repos.
- Safety rules demonstrably hold (no execution of untrusted code, no secret leakage).
