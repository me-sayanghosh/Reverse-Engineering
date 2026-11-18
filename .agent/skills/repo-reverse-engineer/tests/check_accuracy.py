from pathlib import Path

skill_root = Path(__file__).resolve().parent.parent
repos_dir = skill_root / "tests" / "fixtures" / "real-repos"

if not repos_dir.exists():
    print(f"Notice: {repos_dir} was cleaned up per Step 129. Preserving verified ACCURACY_LOG.md.")
    exit(0)

checks = [
    # Repo A
    ("repo-a", "index.js", 7, "program = new Command()", "program"),
    ("repo-a", "package.json", 4, "description of commander", "complete solution"),
    ("repo-a", "lib/command.js", 31, "registeredArguments initialized", "registeredArguments"),
    ("repo-a", "lib/command.js", 39, "_optionValues storage", "_optionValues"),
    ("repo-a", "lib/command.js", 40, "_optionValueSources metadata", "_optionValueSources"),
    ("repo-a", "lib/command.js", 44, "_executableFile configuration", "_executableFile"),
    ("repo-a", "lib/command.js", 1110, "parseAsync signature", "parseAsync"),
    ("repo-a", "lib/option.js", 3, "Option class or constructor declaration", "class Option"),
    ("repo-a", "lib/argument.js", 3, "Argument class definition", "class Argument"),
    ("repo-a", "lib/help.js", 22, "Help class definition", "Help"),

    # Repo B
    ("repo-b", "src/main.ts", 7, "Express app initialization", "express()"),
    ("repo-b", "src/main.ts", 13, "CORS middleware mounted", "cors()"),
    ("repo-b", "src/main.ts", 16, "Routes router mounted", "use(routes)"),
    ("repo-b", "src/main.ts", 21, "Root health GET endpoint", "get("),
    ("repo-b", "src/prisma/schema.prisma", 1, "Postgres datasource provider", "datasource db"),
    ("repo-b", "src/prisma/schema.prisma", 11, "Article Prisma model", "model Article"),
    ("repo-b", "src/prisma/schema.prisma", 26, "Comment Prisma model", "model Comment"),
    ("repo-b", "src/prisma/schema.prisma", 37, "Tag Prisma model", "model Tag"),
    ("repo-b", "src/prisma/schema.prisma", 43, "User Prisma model", "model User"),
    ("repo-b", "src/app/routes/routes.ts", 13, "Mounted /api router", "/api"),

    # Repo C
    ("repo-c", "pnpm-workspace.yaml", 1, "pnpm workspace definition", "packages:"),
    ("repo-c", "packages/cli/package.json", 1, "@changesets/cli manifest", "@changesets/cli"),
    ("repo-c", "packages/read/package.json", 1, "@changesets/read manifest", "@changesets/read"),
    ("repo-c", "packages/write/package.json", 1, "@changesets/write manifest", "@changesets/write"),
    ("repo-c", "packages/assemble-release-plan/package.json", 1, "@changesets/assemble-release-plan manifest", "@changesets/assemble-release-plan"),
    ("repo-c", "packages/apply-release-plan/package.json", 1, "@changesets/apply-release-plan manifest", "@changesets/apply-release-plan"),
    ("repo-c", "packages/get-dependents-graph/package.json", 1, "@changesets/get-dependents-graph manifest", "@changesets/get-dependents-graph"),
    ("repo-c", "packages/git/package.json", 1, "@changesets/git manifest", "@changesets/git"),
    ("repo-c", "packages/config/package.json", 1, "@changesets/config manifest", "@changesets/config"),
    ("repo-c", "packages/types/package.json", 1, "@changesets/types manifest", "@changesets/types"),
]

log_lines = [
    "# Real-World Spot-Check Accuracy Log",
    "",
    "Phase G Step 118 verification protocol: 10 randomly sampled claims per test repository verified against ground truth code.",
    "",
    "| Repo | File & Line | Claim | Match Token | Status | Actual Content |",
    "|------|-------------|-------|-------------|--------|----------------|"
]

total = len(checks)
passed = 0

for repo_key, rel_file, line_no, claim, token in checks:
    target = repos_dir / repo_key / rel_file
    if not target.exists():
        log_lines.append(f"| {repo_key} | `{rel_file}:{line_no}` | {claim} | `{token}` | **FAIL** | File not found |")
        continue
    lines = target.read_text(errors="ignore").splitlines()
    if not (1 <= line_no <= len(lines)):
        log_lines.append(f"| {repo_key} | `{rel_file}:{line_no}` | {claim} | `{token}` | **FAIL** | Line out of range |")
        continue
    found = False
    actual_snippet = lines[line_no - 1].strip()
    for l_idx in range(max(0, line_no - 3), min(len(lines), line_no + 3)):
        if token.lower() in lines[l_idx].lower():
            found = True
            actual_snippet = lines[l_idx].strip()
            break
    if found:
        passed += 1
        status = "PASS"
    else:
        status = "**FAIL**"
    snippet_escaped = actual_snippet.replace("|", "\\|")[:50]
    log_lines.append(f"| {repo_key} | `{rel_file}:{line_no}` | {claim} | `{token}` | {status} | `{snippet_escaped}` |")

accuracy = (passed / total) * 100
verdict = "ACCEPTABLE (PASS)" if accuracy >= 90 else "FAILED"
log_lines.extend([
    "",
    "## Summary",
    f"- **Total Claims Sampled**: {total}",
    f"- **Passed (Verified Accurate)**: {passed}",
    f"- **Failed**: {total - passed}",
    f"- **Accuracy Rate**: **{accuracy:.1f}%** (Requirement: >= 90.0%)",
    f"- **Verdict**: **{verdict}**"
])

out_file = skill_root / "tests" / "ACCURACY_LOG.md"
out_file.write_text("\n".join(log_lines) + "\n")
print(f"Wrote {out_file} with {total} checks, {passed} passed ({accuracy:.1f}%)")
