#!/usr/bin/env python3
"""Tests for Python __main__ entrypoints, Bun/Deno/Fiber server bootstraps, and monorepo frontend roots."""

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import find_entrypoints


class TestPythonMainAndBunBootstrap(unittest.TestCase):
    def test_python_main_guard_entrypoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cli_script = tmp / "src" / "cli_tool.py"
            cli_script.parent.mkdir(parents=True)
            cli_script.write_text(
                """
import sys

def run():
    print("Running CLI tool...")

if __name__ == "__main__":
    run()
""",
                encoding="utf-8",
            )

            entries = find_entrypoints.find_manifest_entrypoints(tmp)
            entry_paths = [e["path"].split(":")[0] for e in entries]
            self.assertIn("src/cli_tool.py", entry_paths)

    def test_bun_and_deno_serve_bootstraps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            bun_server = tmp / "bun_server.ts"
            bun_server.write_text(
                """
export default {
    port: 3000,
    fetch(req) {
        return new Response("Bun Server!");
    },
};

Bun.serve({
    fetch(req) {
        return new Response("Hello from Bun!");
    },
});
""",
                encoding="utf-8",
            )

            deno_server = tmp / "deno_server.ts"
            deno_server.write_text(
                """
Deno.serve({ port: 8000 }, (_req) => {
    return new Response("Hello from Deno!");
});
""",
                encoding="utf-8",
            )

            entries = find_entrypoints.find_server_bootstraps(tmp)
            bootstraps = [e["path"].split(":")[0] for e in entries]
            self.assertIn("bun_server.ts", bootstraps)
            self.assertIn("deno_server.ts", bootstraps)

    def test_go_fiber_and_echo_bootstraps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fiber_app = tmp / "cmd" / "fiber_app.go"
            fiber_app.parent.mkdir(parents=True)
            fiber_app.write_text(
                """package main

func main() {
    app := fiber.New()
    app.Listen(":3000")
}
""",
                encoding="utf-8",
            )

            entries = find_entrypoints.find_server_bootstraps(tmp)
            bootstraps = [e["path"].split(":")[0] for e in entries]
            self.assertIn("cmd/fiber_app.go", bootstraps)

    def test_monorepo_subfolder_frontend_roots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            web_app = tmp / "apps" / "web" / "src" / "App.tsx"
            web_app.parent.mkdir(parents=True)
            web_app.write_text(
                """export default function App() { return <div>Web App</div>; }""",
                encoding="utf-8",
            )

            entries = find_entrypoints.find_frontend_entrypoints(tmp)
            root_paths = [e["path"].split(":")[0] for e in entries]
            self.assertIn("apps/web/src/App.tsx", root_paths)


if __name__ == "__main__":
    unittest.main()
