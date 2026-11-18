#!/usr/bin/env python3
"""Unit tests for find_entrypoints.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FIND_ENTRYPOINTS_PY = SKILL_DIR / "scripts" / "find_entrypoints.py"


class TestFindEntrypoints(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Node app
        pj = {"main": "src/server.js", "bin": {"cli": "bin/run.js"}}
        (self.root / "package.json").write_text(json.dumps(pj))
        (self.root / "src").mkdir()
        (self.root / "bin").mkdir()
        (self.root / "src" / "server.js").write_text(
            "const express = require('express');\nconst app = express();\napp.listen(3000);\n"
        )
        (self.root / "bin" / "run.js").write_text("#!/usr/bin/env node\nconsole.log('cli');\n")

        # Python app
        (self.root / "app.py").write_text(
            "import uvicorn\n\nif __name__ == '__main__':\n    uvicorn.run('app:app')\n"
        )

        # Go app
        (self.root / "cmd" / "api").mkdir(parents=True)
        (self.root / "cmd" / "api" / "main.go").write_text("package main\nfunc main() {}\n")

        # Rust app
        (self.root / "rust_src").mkdir()
        (self.root / "rust_src" / "main.rs").write_text("fn main() {}\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_entrypoints_json(self):
        cmd = ["python3", str(FIND_ENTRYPOINTS_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("root", data)
        self.assertIn("entrypoints", data)

        eps = data["entrypoints"]
        self.assertGreaterEqual(len(eps), 4)

        paths = [e["path"] for e in eps]
        self.assertTrue(any("src/server.js" in p for p in paths), "Node main missing")
        self.assertTrue(any("bin/run.js" in p for p in paths), "Node bin missing")
        self.assertTrue(any("app.py" in p for p in paths), "Python uvicorn bootstrap missing")
        self.assertTrue(any("cmd/api/main.go" in p for p in paths), "Go main missing")

        # Verify citation format file:line
        for ep in eps:
            self.assertIn(":", ep["path"])
            self.assertIn("type", ep)
            self.assertIn("confidence", ep)
            self.assertIn("reason", ep)

    def test_scripts_start_declared_entrypoint(self):
        """Step 47: Verify package.json scripts.start detection."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            pj = {"scripts": {"start": "node dist/server.js"}}
            (r / "package.json").write_text(json.dumps(pj))
            (r / "dist").mkdir()
            (r / "dist" / "server.js").write_text("console.log('started');\n")
            cmd = ["python3", str(FIND_ENTRYPOINTS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            paths = [e["path"] for e in data["entrypoints"]]
            self.assertTrue(any("dist/server.js:1" in p for p in paths))


if __name__ == "__main__":
    unittest.main()
