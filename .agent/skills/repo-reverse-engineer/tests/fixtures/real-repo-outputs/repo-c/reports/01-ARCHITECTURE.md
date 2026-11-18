# 01 - Architecture & Monorepo Package Mapping: changesets

## Monorepo Package Topology
The repository is structured as a pnpm workspace monorepo (`pnpm-workspace.yaml:1`).

```
@changesets/cli (packages/cli/package.json:1)
      │
      ├─► @changesets/read (packages/read/package.json:1)
      ├─► @changesets/parse (packages/parse/package.json:1)
      ├─► @changesets/assemble-release-plan (packages/assemble-release-plan/package.json:1)
      │        └─► @changesets/get-dependents-graph (packages/get-dependents-graph/package.json:1)
      ├─► @changesets/apply-release-plan (packages/apply-release-plan/package.json:1)
      │        └─► @changesets/git (packages/git/package.json:1)
      └─► @changesets/write (packages/write/package.json:1)
```

## Per-Package Roles & Responsibilities
1. **`@changesets/cli`** (`packages/cli/package.json:1`): Main command-line interface entrypoint for `init`, `add`, `version`, `publish`, and `status`.
2. **`@changesets/read`** (`packages/read/package.json:1`): Reads markdown changeset files from the `.changeset/` directory on disk.
3. **`@changesets/parse`** (`packages/parse/package.json:1`): Parses frontmatter and summary content of changeset markdown files into structured objects.
4. **`@changesets/write`** (`packages/write/package.json:1`): Serializes and writes user changeset definitions to `.changeset/*.md`.
5. **`@changesets/assemble-release-plan`** (`packages/assemble-release-plan/package.json:1`): Calculates the topological bump requirements (major/minor/patch) across packages and dependents.
6. **`@changesets/apply-release-plan`** (`packages/apply-release-plan/package.json:1`): Applies version bumps to `package.json` manifests and updates `CHANGELOG.md` files.
7. **`@changesets/get-dependents-graph`** (`packages/get-dependents-graph/package.json:1`): Analyzes inter-package dependencies and constructs reverse dependency graphs.
8. **`@changesets/get-release-plan`** (`packages/get-release-plan/package.json:1`): High-level wrapper coordinating changeset discovery and release planning.
9. **`@changesets/git`** (`packages/git/package.json:1`): Executes git operations (status, diff, tag, commit) for release verification.
10. **`@changesets/config`** (`packages/config/package.json:1`): Parses and validates `.changeset/config.json`.
11. **`@changesets/changelog-git`** (`packages/changelog-git/package.json:1`): Generates changelog entries with git commit hashes.
12. **`@changesets/changelog-github`** (`packages/changelog-github/package.json:1`): Generates changelog entries linking to GitHub PRs and authors.
13. **`@changesets/get-github-info`** (`packages/get-github-info/package.json:1`): GitHub API integration to resolve PR numbers and usernames from commit SHAs.
14. **`@changesets/get-version-range-type`** (`packages/get-version-range-type/package.json:1`): Resolves SemVer range symbols (`^`, `~`, exact).
15. **`@changesets/types`** (`packages/types/package.json:1`): Common TypeScript type definitions (ReleasePlan, ModComp, VersionType).
16. **`@changesets/errors`** (`packages/errors/package.json:1`): Domain-specific exception classes.
17. **`@changesets/logger`** (`packages/logger/package.json:1`): Styled console logging abstractions.
18. **`@changesets/color`** (`packages/color/package.json:1`): ANSI terminal color formatting helpers.
19. **`@changesets/pre`** (`packages/pre/package.json:1`): Lifecycle management for entering and exiting pre-release mode.
20. **`@changesets/should-skip-package`** (`packages/should-skip-package/package.json:1`): Predicate evaluation for private or skipped packages.
21. **`@changesets/release-utils`** (`packages/release-utils/package.json:1`): Shared publishing utilities and npm registry interaction helpers.
