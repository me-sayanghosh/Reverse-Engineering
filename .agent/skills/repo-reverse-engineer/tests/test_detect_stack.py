#!/usr/bin/env python3
"""Unit tests for detect_stack.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DETECT_STACK_PY = SKILL_DIR / "scripts" / "detect_stack.py"


class TestDetectStack(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Create multi-stack fixture
        pj = {
            "dependencies": {
                "express": "^4.18.2",
                "pg": "^8.11.0",
                "redis": "^4.6.0",
            },
            "devDependencies": {
                "jest": "^29.5.0",
            },
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "start": "node index.js",
            },
        }
        (self.root / "package.json").write_text(json.dumps(pj))
        (self.root / "Dockerfile").write_text("FROM node:18-alpine\n")
        (self.root / "docker-compose.yml").write_text("version: '3.8'\nservices:\n  db:\n    image: postgres:15\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_stack_json(self):
        cmd = ["python3", str(DETECT_STACK_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        # Required keys per Step 45
        for key in ["ecosystems", "frameworks", "datastores", "infra", "commands", "confidence"]:
            self.assertIn(key, data, f"Missing key: {key}")

        # Check ecosystems
        self.assertIn("Node/TypeScript", data["ecosystems"])

        # Check frameworks
        self.assertIn("Express", data["frameworks"])
        self.assertIn("Jest", data["frameworks"])

        # Check datastores
        self.assertIn("PostgreSQL", data["datastores"])
        self.assertIn("Redis", data["datastores"])

        # Check infra
        infra_types = [i["type"] for i in data["infra"]]
        self.assertIn("Docker", infra_types)
        self.assertIn("Docker Compose", infra_types)

        # Check commands
        cmds = data["commands"]
        self.assertEqual(cmds.get("install"), "npm install")
        self.assertEqual(cmds.get("build"), "npm run build")
        self.assertEqual(cmds.get("test"), "npm test")
        self.assertEqual(cmds.get("start"), "npm start")

    def test_regression_prisma_datastore_detection(self):
        """Step 119 Regression: ensure schema.prisma datasource provider is detected in datastores."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "package.json").write_text(json.dumps({"name": "test-prisma"}))
            prisma_dir = r / "prisma"
            prisma_dir.mkdir()
            (prisma_dir / "schema.prisma").write_text(
                'datasource db {\n  provider = "postgresql"\n  url = env("DATABASE_URL")\n}\n'
            )
            cmd = ["python3", str(DETECT_STACK_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertIn("PostgreSQL", data["datastores"])

    def test_readme_code_block_command_inference(self):
        """Step 44: Verify command inference from README code blocks."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "requirements-dev.txt").write_text("pytest>=7.0.0\n")
            (r / "README.md").write_text(
                "# My Project\n\n```bash\npip install -r requirements.txt\npython app.py\n```\n"
            )
            cmd = ["python3", str(DETECT_STACK_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            self.assertIn("Python", data["ecosystems"])
            self.assertEqual(data["commands"].get("install"), "pip install -r requirements.txt")
            self.assertEqual(data["commands"].get("start"), "python app.py")


if __name__ == "__main__":
    unittest.main()
