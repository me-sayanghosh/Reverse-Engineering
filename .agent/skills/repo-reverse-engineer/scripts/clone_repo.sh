#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat << 'EOF'
Usage: clone_repo.sh <url|path> [--branch <branch>] [--subdir <subdir>] [--out <dir>] [--max-mb <mb>] [--yes]

Arguments:
  <url|path>         GitHub HTTPS/SSH URL, owner/repo shorthand, or local filesystem path.

Options:
  --branch <branch>  Specific branch, tag, or commit to clone.
  --subdir <subdir>  Subdirectory to sparsely check out.
  --out <dir>        Destination directory for clone/metadata.
  --max-mb <mb>      Maximum repository size in MB (default: 500).
  --yes              Skip size confirmation prompt.
  -h, --help         Show this help message and exit.
EOF
}

TARGET=""
BRANCH=""
SUBDIR=""
OUT_DIR=""
MAX_MB=500
YES=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --branch)
            if [[ $# -lt 2 || "$2" == -* ]]; then
                echo "Error: Invalid or missing branch argument" >&2
                exit 1
            fi
            BRANCH="$2"
            shift 2
            ;;
        --subdir)
            if [[ $# -lt 2 || "$2" == -* ]]; then
                echo "Error: Invalid or missing subdir argument" >&2
                exit 1
            fi
            SUBDIR="$2"
            shift 2
            ;;
        --out)
            if [[ $# -lt 2 || "$2" == -* ]]; then
                echo "Error: Invalid or missing out argument" >&2
                exit 1
            fi
            OUT_DIR="$2"
            shift 2
            ;;
        --max-mb)
            if [[ $# -lt 2 ]] || ! [[ "$2" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                echo "Error: Invalid or missing --max-mb argument '$2'" >&2
                exit 1
            fi
            MAX_MB="$2"
            shift 2
            ;;
        --yes)
            YES=1
            shift
            ;;
        -*)
            echo "Error: Unknown option $1" >&2
            usage >&2
            exit 1
            ;;
        *)
            if [[ -z "$TARGET" ]]; then
                TARGET="$1"
                shift
            else
                echo "Error: Unexpected argument $1" >&2
                usage >&2
                exit 1
            fi
            ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo "Error: Missing required target <url|path>" >&2
    usage >&2
    exit 1
fi

# Normalize target by stripping trailing slash
TARGET="${TARGET%/}"

TARGET_TYPE=""
CLONE_URL=""
LOCAL_PATH=""
REPO_NAME=""

if [[ -d "$TARGET" ]]; then
    TARGET_TYPE="local"
    LOCAL_PATH="$(cd "$TARGET" && pwd)"
    REPO_NAME="$(basename "$LOCAL_PATH")"
elif [[ "$TARGET" =~ ^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)((\.git)?/?)$ ]]; then
    TARGET_TYPE="github_https"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    CLONE_URL="https://github.com/${BASH_REMATCH[1]}/${REPO_NAME}.git"
elif [[ "$TARGET" =~ ^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)((\.git)?/?)$ ]]; then
    TARGET_TYPE="github_ssh"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    CLONE_URL="git@github.com:${BASH_REMATCH[1]}/${REPO_NAME}.git"
elif [[ "$TARGET" =~ ^https?://gitlab\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)((\.git)?/?)$ ]]; then
    TARGET_TYPE="gitlab_https"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    CLONE_URL="https://gitlab.com/${BASH_REMATCH[1]}/${REPO_NAME}.git"
elif [[ "$TARGET" =~ ^https?://bitbucket\.org/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)((\.git)?/?)$ ]]; then
    TARGET_TYPE="bitbucket_https"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    CLONE_URL="https://bitbucket.org/${BASH_REMATCH[1]}/${REPO_NAME}.git"
elif [[ "$TARGET" =~ ^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)((\.git)?/?)$ ]]; then
    TARGET_TYPE="shorthand"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
    CLONE_URL="https://github.com/${BASH_REMATCH[1]}/${REPO_NAME}.git"
else
    echo "Error: Invalid target '$TARGET'. Must be a GitHub URL, owner/repo shorthand, or existing local directory." >&2
    exit 1
fi

echo "Validated target: type=$TARGET_TYPE, repo=$REPO_NAME"

if [[ -z "$OUT_DIR" ]]; then
    OUT_DIR="reverse-engineered/$REPO_NAME"
fi
mkdir -p "$OUT_DIR"

if [[ "$TARGET_TYPE" == "local" ]]; then
    echo "Local mode: using repository at $LOCAL_PATH"
    echo "Output directory: $OUT_DIR"
fi

check_repo_size() {
    if [[ "$TARGET_TYPE" != "local" ]]; then
        python3 - << PYEOF
import sys, urllib.request, json, re

clone_url = "$CLONE_URL"
max_mb = float("$MAX_MB")
skip_confirm = int("$YES")

match = re.search(r"github\.com[:/]([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?$", clone_url)
if not match:
    sys.exit(0)

owner, repo = match.group(1), match.group(2)
api_url = f"https://api.github.com/repos/{owner}/{repo}"

try:
    req = urllib.request.Request(api_url, headers={"User-Agent": "repo-reverse-engineer"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
        size_kb = data.get("size", 0)
        size_mb = size_kb / 1024.0
        if size_mb > max_mb and not skip_confirm:
            print(f"Error: Repository {owner}/{repo} size (~{size_mb:.1f} MB) exceeds limit of {max_mb:.0f} MB.", file=sys.stderr)
            print("To proceed anyway, re-run with --yes.", file=sys.stderr)
            sys.exit(2)
        elif size_mb > max_mb and skip_confirm:
            print(f"Notice: Repository size (~{size_mb:.1f} MB) exceeds {max_mb:.0f} MB, continuing due to --yes.")
except urllib.error.HTTPError as e:
    # 404/403: might be private or rate limited; let git clone attempt and report auth error
    pass
except Exception:
    pass
PYEOF
    fi
}

check_repo_size

REPO_DIR="$OUT_DIR"
if [[ "$TARGET_TYPE" == "local" ]]; then
    REPO_DIR="$LOCAL_PATH"
else
    CLONE_ARGS=(--depth 1)
    if [[ -n "$BRANCH" ]]; then
        CLONE_ARGS+=(--branch "$BRANCH")
    fi
    if [[ -n "$SUBDIR" ]]; then
        CLONE_ARGS+=(--filter=blob:none --sparse)
    fi

    # Remove empty OUT_DIR if it was created so git clone can populate it
    if [[ -d "$OUT_DIR" ]] && [[ -z "$(ls -A "$OUT_DIR" 2>/dev/null)" ]]; then
        rmdir "$OUT_DIR"
    fi

    CLONE_OUTPUT=""
    if ! CLONE_OUTPUT=$(git clone "${CLONE_ARGS[@]}" "$CLONE_URL" "$OUT_DIR" 2>&1); then
        if echo "$CLONE_OUTPUT" | grep -qiE "Could not resolve host|Failed to connect"; then
            echo "Error: Network failure connecting to remote host." >&2
        elif echo "$CLONE_OUTPUT" | grep -qiE "Remote branch .* not found"; then
            echo "Error: Branch '$BRANCH' not found on remote repository." >&2
        elif echo "$CLONE_OUTPUT" | grep -qiE "Authentication failed|could not read Username|Repository not found"; then
            echo "Error: Private repository or authentication required for $CLONE_URL." >&2
        else
            echo "Error: Failed to clone repository: $CLONE_OUTPUT" >&2
        fi
        exit 1
    fi

    if [[ -n "$SUBDIR" ]]; then
        git -C "$OUT_DIR" sparse-checkout set "$SUBDIR"
    fi
    echo "Cloned into $OUT_DIR (depth 1)"
fi

detect_license() {
    local target_dir="$1"
    python3 - << PYEOF
import os, sys, glob, re

target_dir = "$target_dir"
patterns = ["LICENSE*", "LICENCE*", "COPYING*", "UNLICENSE*", "license*", "licence*", "copying*", "unlicense*"]
candidates = []
for pat in patterns:
    candidates.extend(glob.glob(os.path.join(target_dir, pat)))
candidates = sorted(list(set(candidates)))
if not candidates:
    print("none\tnone")
    sys.exit(0)

lic_file = os.path.basename(candidates[0])
spdx = "none"
try:
    with open(candidates[0], "r", encoding="utf-8", errors="ignore") as f:
        head = "".join([f.readline() for _ in range(40)])
        head_lower = head.lower()
        if "mit license" in head_lower or "permission is hereby granted, free of charge" in head_lower:
            spdx = "MIT"
        elif "apache license" in head_lower and "2.0" in head_lower:
            spdx = "Apache-2.0"
        elif "affero general public license" in head_lower:
            spdx = "AGPL-3.0"
        elif "lesser general public license" in head_lower:
            spdx = "LGPL"
        elif "gnu general public license" in head_lower:
            spdx = "GPL"
        elif "bsd 2-clause" in head_lower:
            spdx = "BSD-2-Clause"
        elif "bsd 3-clause" in head_lower or "redistribution and use in source and binary forms" in head_lower:
            spdx = "BSD"
        elif "mozilla public license" in head_lower:
            spdx = "MPL-2.0"
        elif "isc license" in head_lower or "permission to use, copy, modify, and/or distribute this software" in head_lower:
            spdx = "ISC"
        elif "unlicense" in head_lower or "free and unencumbered software released into the public domain" in head_lower:
            spdx = "Unlicense"
        elif "creative commons zero" in head_lower or "cc0 1.0" in head_lower:
            spdx = "CC0-1.0"
        elif "eclipse public license" in head_lower:
            spdx = "EPL-2.0"
        else:
            spdx = "Custom"
except Exception:
    spdx = "none"

print(f"{lic_file}\t{spdx}")
PYEOF
}

LIC_INFO=$(detect_license "$REPO_DIR")
LIC_FILE=$(echo "$LIC_INFO" | cut -f1)
LIC_SPDX=$(echo "$LIC_INFO" | cut -f2)

COMMIT_SHA=$(git -C "$REPO_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")
DETECTED_BRANCH=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
DEFAULT_BRANCH=$(git -C "$REPO_DIR" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "$DETECTED_BRANCH")

if [[ -z "$DEFAULT_BRANCH" || "$DEFAULT_BRANCH" == "unknown" ]]; then
    DEFAULT_BRANCH="$DETECTED_BRANCH"
fi

CLONE_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

META_OUT_DIR="$OUT_DIR" \
META_URL="${CLONE_URL:-$LOCAL_PATH}" \
META_SHA="$COMMIT_SHA" \
META_BRANCH="${BRANCH:-$DETECTED_BRANCH}" \
META_DATE="$CLONE_DATE" \
META_LIC_FILE="$LIC_FILE" \
META_LIC_SPDX="$LIC_SPDX" \
META_DEF_BRANCH="$DEFAULT_BRANCH" \
python3 - << 'PYEOF'
import json, os

out_dir = os.environ.get("META_OUT_DIR", "")
lic_file = os.environ.get("META_LIC_FILE", "none")

meta = {
    "url": os.environ.get("META_URL", ""),
    "commit_sha": os.environ.get("META_SHA", "unknown"),
    "branch": os.environ.get("META_BRANCH", "unknown"),
    "clone_date": os.environ.get("META_DATE", ""),
    "license_file_detected": lic_file if lic_file != "none" else None,
    "license_spdx": os.environ.get("META_LIC_SPDX", "none"),
    "default_branch": os.environ.get("META_DEF_BRANCH", "unknown"),
}

target_path = os.path.join(out_dir, "repo_meta.json")
with open(target_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
print(f"Wrote metadata to {target_path}")
PYEOF
