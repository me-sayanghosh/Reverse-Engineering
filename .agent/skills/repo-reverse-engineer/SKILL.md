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
