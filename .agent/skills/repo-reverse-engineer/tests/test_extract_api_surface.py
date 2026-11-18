#!/usr/bin/env python3
"""Unit tests for extract_api_surface.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
EXTRACT_API_PY = SKILL_DIR / "scripts" / "extract_api_surface.py"


class TestExtractApiSurface(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # 1. Express routes
        (self.root / "routes.ts").write_text(
            'import express from "express";\n'
            'const router = express.Router();\n'
            'router.get("/health", healthCheck);\n'
            'router.post("/auth/login", loginHandler);\n'
            'router.get("/users", requireAuth, listUsers);\n'
        )

        # 2. OpenAPI
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/api/v1/ping": {
                    "get": {"summary": "Ping service"}
                }
            }
        }
        (self.root / "openapi.json").write_text(json.dumps(spec))

        # 3. Proto service
        (self.root / "echo.proto").write_text(
            'syntax = "proto3";\n'
            'service EchoService {\n'
            '  rpc Echo (EchoRequest) returns (EchoResponse);\n'
            '}\n'
        )

        # 4. CLI commands
        (self.root / "cli.js").write_text(
            'program.command("build");\n'
            'program.command("test");\n'
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_api_surface_json(self):
        cmd = ["python3", str(EXTRACT_API_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("routes", data)
        self.assertIn("openapi", data)
        self.assertIn("grpc", data)
        self.assertIn("cli_commands", data)

        # Check routes
        routes = data["routes"]
        paths = [r["path"] for r in routes]
        self.assertIn("/health", paths)
        self.assertIn("/auth/login", paths)
        self.assertIn("/users", paths)

        # Check auth tagging
        user_route = next(r for r in routes if r["path"] == "/users")
        self.assertTrue(user_route["auth_required"])

        # Check openapi
        openapi = data["openapi"]
        self.assertEqual(len(openapi), 1)
        self.assertEqual(openapi[0]["path"], "/api/v1/ping")

        # Check grpc
        grpc = data["grpc"]
        self.assertEqual(len(grpc), 1)
        self.assertEqual(grpc[0]["rpc"], "Echo")

        # Check cli
        cli = data["cli_commands"]
        cmd_names = [c["command"] for c in cli]
        self.assertIn("build", cmd_names)
        self.assertIn("test", cmd_names)

    def test_flask_and_human_readable_output(self):
        """Rule 8 & Step 66: Verify Flask blueprint routes and human-readable output."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "api.py").write_text(
                "from flask import Blueprint\n"
                "bp = Blueprint('api', __name__)\n"
                "@bp.route('/items', methods=['POST', 'PUT'])\n"
                "def save_item(): pass\n"
            )
            # Test human readable (no --json)
            cmd = ["python3", str(EXTRACT_API_PY), str(r)]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertIn("HTTP Routes Discovered", res.stdout)
            self.assertIn("/items", res.stdout)
            self.assertIn("POST/PUT", res.stdout)


if __name__ == "__main__":
    unittest.main()
