#!/usr/bin/env python3
"""Tests for GCP, SendGrid, Anthropic secrets detection, Dockerfile ENV extraction, and python-decouple."""

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import scan_secrets_env


class TestGcpAndSendGridSecrets(unittest.TestCase):
    def test_gcp_api_key_detection_and_masking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cfg_file = tmp / "config.py"
            # 39-character AIza key
            cfg_file.write_text('GOOGLE_KEY = "AIzaSyD12345678901234567890123456789012"\n', encoding="utf-8")

            findings = scan_secrets_env.detect_potential_secrets(tmp)
            self.assertEqual(len(findings), 1)
            f = findings[0]
            self.assertEqual(f["type"], "Google API Key")
            self.assertTrue(f["masked_sample"].startswith("AIza"))
            self.assertTrue(f["masked_sample"].endswith("****"))
            self.assertNotIn("SyD1234567890", f["masked_sample"])

    def test_sendgrid_and_anthropic_secrets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            env_file = tmp / "service.js"
            sg_key = "SG." + ("a" * 22) + "." + ("b" * 43)
            ant_key = "sk-ant-api03-" + ("c" * 32)
            env_file.write_text(
                f"""
const sendgridKey = "{sg_key}";
const anthropicKey = "{ant_key}";
""",
                encoding="utf-8",
            )

            findings = scan_secrets_env.detect_potential_secrets(tmp)
            types = {f["type"] for f in findings}
            self.assertIn("SendGrid API Key", types)
            self.assertIn("Anthropic API Key", types)

            for f in findings:
                self.assertTrue(f["masked_sample"].endswith("****"))

    def test_dockerfile_env_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            df = tmp / "Dockerfile"
            df.write_text(
                """
FROM python:3.11-slim
ENV APP_PORT=8080
ENV DATABASE_URL=postgres://localhost:5432/app
ENV SENTRY_DSN=https://example.com/123
CMD ["python", "main.py"]
""",
                encoding="utf-8",
            )

            env_vars = scan_secrets_env.find_env_vars(tmp)
            var_names = {v["name"]: v for v in env_vars}
            self.assertIn("APP_PORT", var_names)
            self.assertIn("DATABASE_URL", var_names)
            self.assertIn("SENTRY_DSN", var_names)

            self.assertEqual(var_names["APP_PORT"]["category"], "infra")
            self.assertEqual(var_names["DATABASE_URL"]["category"], "db")
            self.assertEqual(var_names["SENTRY_DSN"]["category"], "third-party")

    def test_decouple_and_django_environ(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            settings_py = tmp / "settings.py"
            settings_py.write_text(
                """
from decouple import config
import environ

env = environ.Env()

SECRET_KEY = config('DJANGO_SECRET_KEY')
REDIS_HOST = env.str('REDIS_HOST')
DEBUG = env.bool('DEBUG', default=False)
""",
                encoding="utf-8",
            )

            env_vars = scan_secrets_env.find_env_vars(tmp)
            var_names = {v["name"]: v for v in env_vars}
            self.assertIn("DJANGO_SECRET_KEY", var_names)
            self.assertIn("REDIS_HOST", var_names)
            self.assertIn("DEBUG", var_names)


if __name__ == "__main__":
    unittest.main()
