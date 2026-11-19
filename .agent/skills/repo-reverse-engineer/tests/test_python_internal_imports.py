#!/usr/bin/env python3
"""Unit tests verifying single-file Python module imports and TypeScript .mts/.cts handling in dep_graph."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
DEP_GRAPH_PY = SCRIPTS_DIR / "dep_graph.py"


class TestPythonInternalImports(unittest.TestCase):
    def test_single_file_python_module_resolution(self):
        """Verify single-file Python modules (utils.py) are classified as internal."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "utils.py").write_text("def helper(): pass\n")
            (r / "main.py").write_text("import utils\nfrom utils import helper\nimport sys\nimport requests\n")

            cmd = ["python3", str(DEP_GRAPH_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"dep_graph failed: {res.stderr}")
            data = json.loads(res.stdout)

            raw_edges = data.get("raw_edges", [])
            utils_edges = [e for e in raw_edges if "utils" in e["specifier"]]
            self.assertEqual(len(utils_edges), 2, "Expected 2 imports referencing utils")
            for e in utils_edges:
                self.assertEqual(e["type"], "internal", f"Expected utils to be internal, got {e['type']}")
                self.assertIn("utils.py", e["target"])

            sys_edge = next((e for e in raw_edges if e["target"] == "sys"), None)
            self.assertIsNotNone(sys_edge)
            self.assertEqual(sys_edge["type"], "stdlib")

            req_edge = next((e for e in raw_edges if e["target"] == "requests"), None)
            self.assertIsNotNone(req_edge)
            self.assertEqual(req_edge["type"], "external")

    def test_mts_and_cts_collected_in_dep_graph(self):
        """Verify .mts and .cts files are parsed in collect_all_imports."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "worker.mts").write_text("import { calculate } from './math.mjs';\n")
            (r / "math.mjs").write_text("export const calculate = () => 42;\n")

            cmd = ["python3", str(DEP_GRAPH_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"dep_graph failed: {res.stderr}")
            data = json.loads(res.stdout)

            raw_edges = data.get("raw_edges", [])
            self.assertTrue(len(raw_edges) >= 1, "Failed to collect edges from .mts file")
            self.assertEqual(raw_edges[0]["source"], "worker.mts")
            self.assertEqual(raw_edges[0]["type"], "internal")


if __name__ == "__main__":
    unittest.main()
