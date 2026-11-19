#!/usr/bin/env python3
"""Unit tests verifying Go cmd/main.go, func main(), and .tsx server bootstrap in find_entrypoints."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
FIND_ENTRYPOINTS_PY = SCRIPTS_DIR / "find_entrypoints.py"


class TestEntrypointsGoAndTsx(unittest.TestCase):
    def test_cmd_main_go_and_func_main(self):
        """Verify Go cmd/main.go and custom main packages with func main() are discovered."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "cmd").mkdir()
            (r / "cmd" / "main.go").write_text("package main\nfunc main() {}\n")
            (r / "server").mkdir()
            (r / "server" / "app.go").write_text("package main\nimport \"fmt\"\nfunc main() { fmt.Println() }\n")

            cmd = ["python3", str(FIND_ENTRYPOINTS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"find_entrypoints failed: {res.stderr}")
            data = json.loads(res.stdout)

            paths = [e["path"] for e in data.get("entrypoints", [])]
            self.assertTrue(any("cmd/main.go" in p for p in paths), "cmd/main.go was not detected as entrypoint")
            self.assertTrue(any("server/app.go" in p for p in paths), "server/app.go with func main() was not detected")

    def test_tsx_server_bootstrap_and_nextjs_src_app(self):
        """Verify server bootstrap in .tsx and Next.js src/app layout/page entrypoints."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "src").mkdir()
            (r / "src" / "server.tsx").write_text(
                "import express from 'express';\n"
                "const app = express();\n"
                "app.listen(8080);\n"
            )
            (r / "src" / "app").mkdir()
            (r / "src" / "app" / "layout.tsx").write_text("export default function Layout({ children }) { return children; }\n")

            cmd = ["python3", str(FIND_ENTRYPOINTS_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"find_entrypoints failed: {res.stderr}")
            data = json.loads(res.stdout)

            paths = [e["path"] for e in data.get("entrypoints", [])]
            self.assertTrue(any("src/server.tsx" in p for p in paths), "src/server.tsx bootstrap not detected")
            self.assertTrue(any("src/app/layout.tsx" in p for p in paths), "src/app/layout.tsx Next.js root not detected")


if __name__ == "__main__":
    unittest.main()
