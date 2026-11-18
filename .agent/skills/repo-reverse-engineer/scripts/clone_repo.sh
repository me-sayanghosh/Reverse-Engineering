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
