#!/usr/bin/env python3
"""Unit tests for dep_graph.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEP_GRAPH_PY = SKILL_DIR / "scripts" / "dep_graph.py"


class TestDepGraph(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Create multi-module architecture:
        # api -> services -> db
        (self.root / "api").mkdir()
        (self.root / "services").mkdir()
        (self.root / "db").mkdir()

        (self.root / "db" / "schema.ts").write_text("export interface User { id: string; }")
        (self.root / "services" / "userService.ts").write_text(
            'import { User } from "../db/schema";\nexport function getUser() { return {}; }'
        )
        (self.root / "api" / "routes.ts").write_text(
            'import express from "express";\nimport { getUser } from "../services/userService";\n'
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dep_graph_json(self):
        cmd = ["python3", str(DEP_GRAPH_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("modules", data)
        self.assertIn("module_edges", data)
        self.assertIn("centrality", data)
        self.assertIn("cycles", data)

        modules = data["modules"]
        self.assertIn("api", modules)
        self.assertIn("services", modules)
        self.assertIn("db", modules)

        # Check aggregated module edges
        edge_pairs = [(e["source"], e["target"]) for e in data["module_edges"]]
        self.assertIn(("api", "services"), edge_pairs)
        self.assertIn(("services", "db"), edge_pairs)

        # No cycles in this tree
        self.assertEqual(len(data["cycles"]), 0)

    def test_dep_graph_mermaid(self):
        cmd = ["python3", str(DEP_GRAPH_PY), str(self.root), "--mermaid"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(res.stdout.startswith("graph LR"))
        self.assertIn("-->", res.stdout)

    def test_multiline_and_python_relative_imports(self):
        """Step 56 & 57: Verify multiline JS/TS imports and Python from . import submodule."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            # JS multiline
            (r / "utils.ts").write_text("export const util = 1;\n")
            (r / "app.ts").write_text("import {\n  util\n} from './utils';\nconsole.log(util);\n")

            # Python relative submodule
            pkg = r / "mypkg"
            pkg.mkdir()
            (pkg / "submod.py").write_text("def run(): pass\n")
            (pkg / "caller.py").write_text("from . import submod\n")

            cmd = ["python3", str(DEP_GRAPH_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)
            raw_edges = data.get("raw_edges", [])

            # Check JS multiline
            js_edge = next((e for e in raw_edges if e["source"] == "app.ts"), None)
            self.assertIsNotNone(js_edge, "Multiline JS import was not captured")
            self.assertIn("utils.ts", js_edge["target"])

            # Check Python relative submodule
            py_edge = next((e for e in raw_edges if e["source"] == "mypkg/caller.py"), None)
            self.assertIsNotNone(py_edge, "Python relative submodule import was not captured")
            self.assertIn("mypkg/submod.py", py_edge["target"])


if __name__ == "__main__":
    unittest.main()
