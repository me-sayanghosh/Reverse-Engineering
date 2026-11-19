#!/usr/bin/env python3
"""Unit tests verifying ecosystem parser extensions and audit fixes."""

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

import _common
DETECT_STACK_PY = SCRIPTS_DIR / "detect_stack.py"
DEP_GRAPH_PY = SCRIPTS_DIR / "dep_graph.py"


class TestAuditExtensions(unittest.TestCase):
    def test_lockfile_case_insensitivity(self):
        """Verify is_lockfile identifies lockfiles regardless of case."""
        self.assertTrue(_common.is_lockfile("package-lock.json"))
        self.assertTrue(_common.is_lockfile("PACKAGE-LOCK.JSON"))
        self.assertTrue(_common.is_lockfile("bun.lock"))
        self.assertTrue(_common.is_lockfile("mix.lock"))
        self.assertTrue(_common.is_lockfile("Cargo.lock.dist"))
        self.assertFalse(_common.is_lockfile("normal_file.js"))

    def test_minified_extensions(self):
        """Verify is_minified catches modern chunk and bundle extensions."""
        self.assertTrue(_common.is_minified("app.chunk.js"))
        self.assertTrue(_common.is_minified("index.bundle.mjs"))
        self.assertTrue(_common.is_minified("vendor.min.cjs"))
        self.assertFalse(_common.is_minified("app.js"))

    def test_utf16_bom_text_not_binary(self):
        """Verify UTF-16 files with BOM are not falsely identified as binary."""
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            # UTF-16 LE text "Hello world\n"
            content = "Hello world\n".encode("utf-16")
            tf.write(content)
            tf_path = Path(tf.name)
        try:
            self.assertFalse(_common.is_binary(tf_path), "UTF-16 text file falsely classified as binary")
        finally:
            tf_path.unlink()

    def test_modern_manifests_and_frameworks(self):
        """Verify detect_stack detects Deno, Bun, Elixir Phoenix, and Swift Vapor."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "deno.json").write_text('{"tasks": {"start": "deno run main.ts"}}\n')
            (r / "mix.exs").write_text('defp deps do [{:phoenix, "~> 1.7"}] end\n')
            (r / "Package.swift").write_text('// swift-tools-version:5.7\n.package(url: "https://github.com/vapor/vapor.git")\n')

            cmd = ["python3", str(DETECT_STACK_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"detect_stack failed: {res.stderr}")
            data = json.loads(res.stdout)

            ecosystems = data.get("ecosystems", [])
            self.assertIn("Deno/TypeScript", ecosystems)
            self.assertIn("Elixir", ecosystems)
            self.assertIn("Swift", ecosystems)

            frameworks = data.get("frameworks", [])
            self.assertIn("Phoenix", frameworks)
            self.assertIn("Vapor", frameworks)

    def test_cpp_and_swift_imports_in_dep_graph(self):
        """Verify dep_graph parses C/C++ #include and Swift import statements."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "src").mkdir()
            (r / "src" / "engine.hpp").write_text("#pragma once\nclass Engine {};\n")
            (r / "src" / "main.cpp").write_text('#include <iostream>\n#include "engine.hpp"\nint main() {}\n')
            (r / "App.swift").write_text("import Foundation\nimport SwiftUI\nimport MyCustomModule\n")

            cmd = ["python3", str(DEP_GRAPH_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"dep_graph failed: {res.stderr}")
            data = json.loads(res.stdout)

            raw_edges = data.get("raw_edges", [])
            cpp_internal = next((e for e in raw_edges if e["source"] == "src/main.cpp" and e["type"] == "internal"), None)
            self.assertIsNotNone(cpp_internal, "Internal C++ #include was not captured")
            self.assertIn("engine.hpp", cpp_internal["target"])

            swift_stdlib = next((e for e in raw_edges if e["source"] == "App.swift" and e["target"] == "SwiftUI"), None)
            self.assertIsNotNone(swift_stdlib, "SwiftUI stdlib import missing")
            self.assertEqual(swift_stdlib["type"], "stdlib")

    def test_ts_path_alias_resolution(self):
        """Verify dep_graph resolves @/ TypeScript path aliases to src/ files."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "src" / "components").mkdir(parents=True)
            (r / "src" / "components" / "Button.tsx").write_text("export const Button = () => null;\n")
            (r / "src" / "App.tsx").write_text("import { Button } from '@/components/Button';\n")

            cmd = ["python3", str(DEP_GRAPH_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0)
            data = json.loads(res.stdout)

            raw_edges = data.get("raw_edges", [])
            alias_edge = next((e for e in raw_edges if e["source"] == "src/App.tsx"), None)
            self.assertIsNotNone(alias_edge, "@/ path alias import was not resolved")
            self.assertEqual(alias_edge["type"], "internal")
            self.assertIn("Button.tsx", alias_edge["target"])


if __name__ == "__main__":
    unittest.main()
