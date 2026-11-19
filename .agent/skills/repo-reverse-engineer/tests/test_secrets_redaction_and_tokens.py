#!/usr/bin/env python3
"""Unit tests verifying secret token patterns, placeholder filtering, and URI scheme preservation in scan_secrets_env."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SCAN_SECRETS_PY = SCRIPTS_DIR / "scan_secrets_env.py"


class TestSecretsRedactionAndTokens(unittest.TestCase):
    def test_uri_preservation_in_redaction(self):
        """Verify redacting a DB URI preserves the protocol and hostname."""
        import sys
        sys.path.insert(0, str(SCRIPTS_DIR))
        import scan_secrets_env

        uri = "DATABASE_URL=postgres://admin:SuperSecretPassword123@db.internal:5432/prod"
        redacted = scan_secrets_env.redact_all_secrets_filter(uri)
        self.assertIn("postgres://admin:", redacted)
        self.assertIn("@db.internal:5432/prod", redacted)
        self.assertNotIn("SuperSecretPassword123", redacted)
        self.assertIn("Su****", redacted)

    def test_gitlab_npm_and_pypi_tokens(self):
        """Verify GitLab PAT, npm token, and PyPI token detection."""
        gl_tok = "gl" + "pat-" + "abcdef1234567890ABCD"
        npm_tok = "npm_" + "1234567890abcdef1234567890abcdef12"
        pypi_tok = "pypi-" + "AgEIcHlwaS5vcmcCJDEyMzQ1Njc4LTkwYWItY2RlZi0xMjM0LTU2Nzg5MGFiY2RlZgACKls"
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "tokens.txt").write_text(
                f"GL_TOKEN={gl_tok}\n"
                f"NPM_TOKEN={npm_tok}\n"
                f"PYPI_TOKEN={pypi_tok}\n"
            )

            cmd = ["python3", str(SCAN_SECRETS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"scan_secrets failed: {res.stderr}")

            # Verify raw secret strings are strictly excluded
            self.assertNotIn("abcdef1234567890ABCD", res.stdout)
            self.assertNotIn("1234567890abcdef1234567890abcdef12", res.stdout)

            data = json.loads(res.stdout)
            findings = data.get("secret_findings", [])
            types = {f["type"] for f in findings}
            self.assertIn("GitLab Personal Access Token", types)
            self.assertIn("npm Access Token", types)
            self.assertIn("PyPI API Token", types)

    def test_placeholder_filtering(self):
        """Verify changeme, dummy, and placeholder tokens are not flagged as real secrets."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "dummy.env").write_text(
                "API_KEY=changeme_123456789012\n"
                "SECRET_TOKEN=dummy_token_placeholder_for_tests\n"
            )

            cmd = ["python3", str(SCAN_SECRETS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            findings = data.get("secret_findings", [])
            self.assertEqual(len(findings), 0, f"Placeholders were falsely flagged: {findings}")


if __name__ == "__main__":
    unittest.main()
