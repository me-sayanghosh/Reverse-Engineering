#!/usr/bin/env python3
"""Cross-platform check: ensure no hard-coded POSIX paths in scripts."""

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"


class TestCrossPlatform(unittest.TestCase):
    def test_no_hardcoded_posix_paths(self):
        forbidden_patterns = [
            r"(/tmp[/\s'\"])",
            r"(/home[/\s'\"])",
            r"(/Users/[a-zA-Z0-9_\-]+)",
        ]
        violations = []

        for script in SCRIPTS_DIR.glob("*"):
            if script.is_file() and not script.name.startswith("."):
                content = script.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden_patterns:
                    matches = re.findall(pat, content)
                    if matches:
                        violations.append(f"{script.name}: matches forbidden pattern {pat}")

        self.assertEqual(violations, [], f"Found hard-coded user/system paths: {violations}")


if __name__ == "__main__":
    unittest.main()
