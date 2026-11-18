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
            BRANCH="$2"
            shift 2
            ;;
        --subdir)
            SUBDIR="$2"
            shift 2
            ;;
        --out)
            OUT_DIR="$2"
            shift 2
            ;;
        --max-mb)
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

TARGET_TYPE=""
CLONE_URL=""
LOCAL_PATH=""
REPO_NAME=""

if [[ -d "$TARGET" ]]; then
    TARGET_TYPE="local"
    LOCAL_PATH="$(cd "$TARGET" && pwd)"
    REPO_NAME="$(basename "$LOCAL_PATH")"
elif [[ "$TARGET" =~ ^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?$ ]]; then
    TARGET_TYPE="github_https"
    CLONE_URL="$TARGET"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
elif [[ "$TARGET" =~ ^git@github\.com:([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)(\.git)?$ ]]; then
    TARGET_TYPE="github_ssh"
    CLONE_URL="$TARGET"
    REPO_NAME="${BASH_REMATCH[2]%.git}"
elif [[ "$TARGET" =~ ^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$ ]]; then
    TARGET_TYPE="shorthand"
    CLONE_URL="https://github.com/$TARGET.git"
    REPO_NAME="${BASH_REMATCH[2]}"
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
