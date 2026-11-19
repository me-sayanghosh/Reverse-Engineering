#!/usr/bin/env python3
"""Unit tests verifying edge cases in secret masking, config parsing, and entrypoint discovery."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
import sys
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import scan_secrets_env
SCAN_SECRETS_PY = SCRIPTS_DIR / "scan_secrets_env.py"
FIND_ENTRYPOINTS_PY = SCRIPTS_DIR / "find_entrypoints.py"


class TestSecretsAndEntrypointsEdgeCases(unittest.TestCase):
    def test_mask_secret_short_string_boundaries(self):
        """Verify mask_secret never leaks short secret bytes."""
        self.assertEqual(scan_secrets_env.mask_secret("ab"), "****")
        self.assertEqual(scan_secrets_env.mask_secret("a"), "****")
        self.assertEqual(scan_secrets_env.mask_secret(""), "****")
        self.assertEqual(scan_secrets_env.mask_secret("abc"), "a****")
        self.assertEqual(scan_secrets_env.mask_secret("abcd"), "a****")
        self.assertEqual(scan_secrets_env.mask_secret("AKIA1234567890EXAMPLE", 4), "AKIA****")

    def test_db_uri_and_openai_secrets_detection(self):
        """Verify secrets in database URIs and OpenAI keys are detected and redacted."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "config.env").write_text(
                "DATABASE_URL=postgres://admin:SuperSecretPassword123@db.internal:5432/prod\n"
                "AI_KEY=sk-proj-1234567890abcdef1234567890abcdef\n"
            )

            cmd = ["python3", str(SCAN_SECRETS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"scan_secrets failed: {res.stderr}")

            # Verify raw secret strings are completely excluded
            self.assertNotIn("SuperSecretPassword123", res.stdout)
            self.assertNotIn("1234567890abcdef1234567890abcdef", res.stdout)

            data = json.loads(res.stdout)
            findings = data.get("secret_findings", [])
            types = [f["type"] for f in findings]
            self.assertTrue(any("Database" in t for t in types), "DB URI password not flagged")
            self.assertTrue(any("OpenAI" in t or "AI" in t for t in types), "OpenAI key not flagged")

    def test_esm_exports_and_django_entrypoints(self):
        """Verify find_entrypoints detects package.json exports field and Django manage.py."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            # Node app with exports field but no main field
            (r / "package.json").write_text(json.dumps({
                "name": "esm-app",
                "exports": {
                    ".": "./dist/index.js",
                    "./cli": "./bin/run.js"
                }
            }))
            (r / "dist").mkdir()
            (r / "dist" / "index.js").write_text("console.log('esm index');\n")

            # Django manage.py
            (r / "manage.py").write_text("#!/usr/bin/env python\nimport os\n")

            cmd = ["python3", str(FIND_ENTRYPOINTS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"find_entrypoints failed: {res.stderr}")
            data = json.loads(res.stdout)

            paths = [e["path"] for e in data.get("entrypoints", [])]
            self.assertTrue(any("dist/index.js" in p for p in paths), "Exports entrypoint dist/index.js missing")
            self.assertTrue(any("manage.py" in p for p in paths), "Django manage.py entrypoint missing")


if __name__ == "__main__":
    unittest.main()
