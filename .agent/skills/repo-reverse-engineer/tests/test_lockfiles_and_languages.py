#!/usr/bin/env python3
"""Tests for modern lockfiles, language extensions, minification, and safe encoding decoders."""

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import _common


class TestLockfilesAndLanguages(unittest.TestCase):
    def test_modern_lockfiles_detected(self):
        lockfiles = [
            "uv.lock",
            "deno.lock",
            "pdm.lock",
            "pixi.lock",
            "conda-lock.yml",
            "gradle.lockfile",
            "sub/dir/UV.LOCK",
            Path("nested/deno.lock"),
        ]
        for lf in lockfiles:
            self.assertTrue(_common.is_lockfile(lf), f"Expected {lf} to be detected as a lockfile")

    def test_modern_language_extensions(self):
        cases = {
            ".elm": "Elm",
            ".cr": "Crystal",
            ".ml": "OCaml",
            ".mli": "OCaml",
            ".re": "ReasonML",
            ".cu": "CUDA",
            ".metal": "Metal",
            ".glsl": "GLSL",
            ".frag": "GLSL",
            ".hlsl": "HLSL",
            ".lisp": "Common Lisp",
            ".scm": "Scheme",
            ".rkt": "Racket",
            ".purs": "PureScript",
            ".cbl": "COBOL",
            ".f90": "Fortran",
            ".pas": "Pascal",
            ".d": "D",
            ".vb": "Visual Basic",
        }
        for ext, lang in cases.items():
            self.assertEqual(_common.EXT_TO_LANG.get(ext), lang, f"Extension {ext} mapped to unexpected language")

    def test_modern_minified_extensions(self):
        min_files = [
            "app.min.jsx",
            "index.min.tsx",
            "vendor.bundle.jsx",
            "bundle.bundle.tsx",
            "0.chunk.jsx",
            "main.chunk.tsx",
        ]
        for mf in min_files:
            self.assertTrue(_common.is_minified(mf), f"Expected {mf} to be classified as minified")

    def test_utf32_bom_safe_reading_and_binary_check(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            utf32_file = tmp / "test_utf32.txt"
            content = "Hello UTF-32 World!"
            # Write with UTF-32 LE BOM
            utf32_file.write_bytes(content.encode("utf-32"))
            
            # Should NOT be classified as binary because it is a valid UTF-32 BOM text file
            self.assertFalse(_common.is_binary(utf32_file))
            read_back = _common.read_text_safe(utf32_file)
            self.assertEqual(read_back.strip(), content)

    def test_walk_repo_allows_ci_dotdirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / ".drone").mkdir()
            (tmp / ".drone" / "pipeline.yml").write_text("kind: pipeline\n", encoding="utf-8")
            (tmp / ".husky").mkdir()
            (tmp / ".husky" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            (tmp / ".gitea").mkdir()
            (tmp / ".gitea" / "config.ini").write_text("[app]\nname=test\n", encoding="utf-8")
            (tmp / "node_modules").mkdir()
            (tmp / "node_modules" / "dep.js").write_text("module.exports={}", encoding="utf-8")

            walked = [p.name for p in _common.walk_repo(tmp)]
            self.assertIn("pipeline.yml", walked)
            self.assertIn("pre-commit", walked)
            self.assertIn("config.ini", walked)
            self.assertNotIn("dep.js", walked)


if __name__ == "__main__":
    unittest.main()
