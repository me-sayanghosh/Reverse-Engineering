#!/usr/bin/env python3
"""Unit tests for repo_stats.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_STATS_PY = SKILL_DIR / "scripts" / "repo_stats.py"


class TestRepoStats(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Create fixture files
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("print('hello')\nprint('world')\n")
        (self.root / "src" / "helpers.ts").write_text("export const x = 1;\nexport const y = 2;\n")
        (self.root / "README.md").write_text("# Project Docs\nDescription here\n")

        # Tests dir
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_app.py").write_text("def test_dummy(): pass\n")

        # Docs dir
        (self.root / "docs").mkdir()
        (self.root / "docs" / "guide.md").write_text("# Guide\n")

        # CI config
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / ".github" / "workflows" / "build.yml").write_text("name: CI\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_repo_stats_json_output(self):
        cmd = ["python3", str(REPO_STATS_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("root", data)
        self.assertIn("languages", data)
        self.assertIn("tree", data)
        self.assertIn("largest_files", data)
        self.assertIn("recently_modified", data)
        self.assertIn("markers", data)
        self.assertIn("monorepo", data)

        # Check languages
        langs = data["languages"]
        self.assertIn("Python", langs)
        self.assertIn("TypeScript", langs)
        self.assertIn("Markdown", langs)
        self.assertEqual(langs["Python"]["files"], 2)  # app.py and test_app.py

        # Check markers
        markers = data["markers"]
        self.assertTrue(markers["tests"]["present"])
        self.assertTrue(markers["docs"]["present"])
        self.assertTrue(markers["ci"]["present"])

        # Check largest files
        self.assertGreater(len(data["largest_files"]), 0)
        top_file = data["largest_files"][0]
        self.assertIn("path", top_file)
        self.assertIn("lines", top_file)


if __name__ == "__main__":
    unittest.main()
