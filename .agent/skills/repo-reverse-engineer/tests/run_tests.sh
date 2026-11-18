#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$SKILL_ROOT:$SKILL_ROOT/scripts:${PYTHONPATH:-}"

TEST_FILES=()
for f in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$f" ]; then
        TEST_FILES+=("$f")
    fi
done

TOTAL=${#TEST_FILES[@]}

if [ "$TOTAL" -eq 0 ]; then
    echo "Summary: 0 tests found, 0 passed, 0 failed."
    exit 0
fi

PASSED=0
FAILED=0

echo "Running $TOTAL test file(s)..."
for test_file in "${TEST_FILES[@]}"; do
    test_name="$(basename "$test_file")"
    echo -n "  Running $test_name ... "
    if python3 "$test_file" > /dev/null 2>&1; then
        echo "PASS"
        PASSED=$((PASSED + 1))
    else
        echo "FAIL"
        python3 "$test_file" || true
        FAILED=$((FAILED + 1))
    fi
done

echo "----------------------------------------"
echo "Summary: $TOTAL tests total, $PASSED passed, $FAILED failed."

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
exit 0
