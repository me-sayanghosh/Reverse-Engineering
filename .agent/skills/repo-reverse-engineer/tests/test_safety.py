#!/usr/bin/env python3
"""Safety tests: verifying untrusted code is NOT executed and secrets are masked."""

import json
import subprocess
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DETECT_STACK_PY = SKILL_DIR / "scripts" / "detect_stack.py"
SCAN_SECRETS_PY = SKILL_DIR / "scripts" / "scan_secrets_env.py"
REPO_STATS_PY = SKILL_DIR / "scripts" / "repo_stats.py"
MALICIOUS_FIXTURE = SKILL_DIR / "tests" / "fixtures" / "malicious-repo"


class TestSafety(unittest.TestCase):
    def setUp(self):
        self.canary_file = MALICIOUS_FIXTURE / "PWNED_SHOULD_NEVER_EXIST.txt"
        if self.canary_file.exists():
            self.canary_file.unlink()

    def tearDown(self):
        if self.canary_file.exists():
            self.canary_file.unlink()

    def test_postinstall_is_never_executed(self):
        """Verify static analysis scripts do NOT execute package.json postinstall hooks."""
        # Run detect_stack
        cmd1 = ["python3", str(DETECT_STACK_PY), str(MALICIOUS_FIXTURE), "--json"]
        res1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res1.returncode, 0, f"detect_stack failed: {res1.stderr}")

        # Run repo_stats
        cmd2 = ["python3", str(REPO_STATS_PY), str(MALICIOUS_FIXTURE), "--json"]
        res2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res2.returncode, 0, f"repo_stats failed: {res2.stderr}")

        # Assert canary file was NOT created
        self.assertFalse(
            self.canary_file.exists(),
            "CRITICAL SECURITY FAILURE: postinstall hook was executed during analysis!",
        )

        # Assert suspicious hook was flagged
        data1 = json.loads(res1.stdout)
        suspicious = data1.get("suspicious_scripts", [])
        self.assertTrue(len(suspicious) > 0, "Suspicious script was not detected in detect_stack output")
        hooks = [s["hook"] for s in suspicious]
        self.assertIn("postinstall", hooks)

    def test_secret_is_masked_and_never_leaked(self):
        """Verify secrets are masked (AKIA****) and never exposed in output."""
        cmd = ["python3", str(SCAN_SECRETS_PY), str(MALICIOUS_FIXTURE), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"scan_secrets failed: {res.stderr}")

        output_str = res.stdout
        # Assert raw fake secrets are completely absent
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", output_str, "Raw AWS key leaked in scan output!")
        self.assertNotIn("mock_super_secret_token_12345", output_str, "Raw secret leaked in scan output!")

        data = json.loads(output_str)
        findings = data.get("secret_findings", [])
        self.assertTrue(len(findings) >= 2, f"Expected at least 2 secret findings, got {len(findings)}")

        # Check masking format
        masked_values = [f.get("masked_sample", "") for f in findings]
        self.assertTrue(any(v.startswith("AKIA****") for v in masked_values), "AWS key not properly masked as AKIA****")
        self.assertTrue(any("mock****" in v for v in masked_values), "Secret not properly masked as mock****")


if __name__ == "__main__":
    unittest.main()
