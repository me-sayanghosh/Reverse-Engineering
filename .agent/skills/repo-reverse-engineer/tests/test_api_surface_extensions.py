#!/usr/bin/env python3
"""Unit tests verifying Go Chi / net-http routes, .tsx route handlers, and auth detection in extract_api_surface."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXTRACT_API_PY = SCRIPTS_DIR / "extract_api_surface.py"


class TestApiSurfaceExtensions(unittest.TestCase):
    def test_go_chi_and_net_http_routes(self):
        """Verify Go Chi PascalCase routes and net/http HandleFunc are extracted."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "main.go").write_text(
                "package main\n"
                "func setup(r chi.Router) {\n"
                "    r.Get(\"/api/v1/health\", HealthCheck)\n"
                "    r.Post(\"/api/v1/login\", LoginHandler)\n"
                "    http.HandleFunc(\"/metrics\", MetricsHandler)\n"
                "}\n"
            )

            cmd = ["python3", str(EXTRACT_API_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_api_surface failed: {res.stderr}")
            data = json.loads(res.stdout)

            routes = data.get("routes", [])
            paths = {rt["path"]: rt["method"] for rt in routes}
            self.assertIn("/api/v1/health", paths)
            self.assertEqual(paths["/api/v1/health"], "GET")
            self.assertIn("/api/v1/login", paths)
            self.assertEqual(paths["/api/v1/login"], "POST")
            self.assertIn("/metrics", paths)
            self.assertEqual(paths["/metrics"], "ANY")

    def test_tsx_and_fastapi_security_routes(self):
        """Verify routes in .tsx files and FastAPI Security/OAuth2 auth flags."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "api.tsx").write_text(
                "import express from 'express';\n"
                "const router = express.Router();\n"
                "router.get('/api/users', (req, res) => res.json([]));\n"
            )
            (r / "main.py").write_text(
                "from fastapi import FastAPI, Security\n"
                "app = FastAPI()\n"
                "@app.get('/secure/data')\n"
                "def get_data(user = Security(get_current_user)):\n"
                "    return {'ok': True}\n"
            )

            cmd = ["python3", str(EXTRACT_API_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_api_surface failed: {res.stderr}")
            data = json.loads(res.stdout)

            routes = data.get("routes", [])
            tsx_route = next((rt for rt in routes if rt["path"] == "/api/users"), None)
            self.assertIsNotNone(tsx_route, "Route in .tsx was not extracted")

            py_route = next((rt for rt in routes if rt["path"] == "/secure/data"), None)
            self.assertIsNotNone(py_route, "FastAPI route /secure/data was not extracted")
            self.assertTrue(py_route["auth_required"], "FastAPI Security() auth was not detected")


if __name__ == "__main__":
    unittest.main()
