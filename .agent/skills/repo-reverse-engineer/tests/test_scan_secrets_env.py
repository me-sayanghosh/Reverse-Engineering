#!/usr/bin/env python3
"""Unit tests for scan_secrets_env.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCAN_SECRETS_PY = SKILL_DIR / "scripts" / "scan_secrets_env.py"


class TestScanSecretsEnv(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # 1. Source file with env and fake secret
        (self.root / "config.py").write_text(
            'import os\n'
            'db_url = os.getenv("DATABASE_URL")\n'
            'jwt_sec = os.environ.get("JWT_SECRET")\n'
            'aws_key = "AKIA1122334455667788"\n'
        )

        # 2. .env.example
        (self.root / ".env.example").write_text(
            "PORT=3000\n"
            "ENABLE_LOGGING=true\n"
            "STRIPE_API_KEY=test_placeholder\n"
        )

        # 3. settings.py
        (self.root / "settings.py").write_text(
            "DEBUG = False\n"
            "ALLOWED_HOSTS = ['localhost']\n"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_scan_secrets_json(self):
        cmd = ["python3", str(SCAN_SECRETS_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("env_vars", data)
        self.assertIn("config_keys", data)
        self.assertIn("secret_findings", data)

        # Verify env categories
        env_dict = {e["name"]: e["category"] for e in data["env_vars"]}
        self.assertEqual(env_dict.get("DATABASE_URL"), "db")
        self.assertEqual(env_dict.get("JWT_SECRET"), "auth")
        self.assertEqual(env_dict.get("PORT"), "infra")
        self.assertEqual(env_dict.get("ENABLE_LOGGING"), "feature-flag")
        self.assertEqual(env_dict.get("STRIPE_API_KEY"), "third-party")

        # Verify secret masking
        findings = data["secret_findings"]
        self.assertGreaterEqual(len(findings), 1)
        aws_finding = next((f for f in findings if "AWS" in f["type"]), None)
        self.assertIsNotNone(aws_finding)
        self.assertEqual(aws_finding["masked_sample"], "AKIA****")

        # Verify redaction guarantee: raw secret never appears
        self.assertNotIn("AKIA1122334455667788", res.stdout)
        self.assertNotIn("1122334455667788", res.stdout)

    def test_modern_env_patterns(self):
        """Step 81: Verify import.meta.env and Go os.LookupEnv patterns."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "client.ts").write_text("const url = import.meta.env.VITE_BACKEND_URL;\n")
            (r / "server.go").write_text('val, ok := os.LookupEnv("DATABASE_PORT")\n')
            cmd = ["python3", str(SCAN_SECRETS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            env_names = {e["name"] for e in data["env_vars"]}
            self.assertIn("VITE_BACKEND_URL", env_names)
            self.assertIn("DATABASE_PORT", env_names)


if __name__ == "__main__":
    unittest.main()
