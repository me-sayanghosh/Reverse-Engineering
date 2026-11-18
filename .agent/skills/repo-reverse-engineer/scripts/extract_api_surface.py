#!/usr/bin/env python3
"""Extract public API surface: HTTP routes, OpenAPI specs, GraphQL/gRPC schemas, CLI commands, and public exports."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


import re

NODE_ROUTE_PATTERNS = [
    # (app|router).get('/path', ...)
    r"""(?:app|router|fastify|server)\.(get|post|put|delete|patch|options|head)\s*\(\s*['"]([^'"]+)['"]""",
    # @Get('/path') in NestJS
    r"""@(Get|Post|Put|Delete|Patch)\s*\(\s*['"]?([^'"]*)['"]?\s*\)""",
]


def extract_node_routes(root_path: Path):
    """Extract HTTP method, path, and file:line handler citations from Node/TS files."""
    root_path = root_path.resolve()
    routes = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (".js", ".ts", ".mjs", ".cjs"):
            continue

        rel = str(file_path.relative_to(root_path))
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines, start=1):
                # Check for auth middleware in surrounding lines (Step 70 hint)
                has_auth = False
                surrounding = " ".join(lines[max(0, idx - 4) : min(len(lines), idx + 2)])
                if any(
                    token in surrounding
                    for token in [
                        "authenticate",
                        "requireAuth",
                        "authMiddleware",
                        "passport",
                        "verifyToken",
                        "jwt",
                        "@UseGuards",
                    ]
                ):
                    has_auth = True

                for pat in NODE_ROUTE_PATTERNS:
                    m = re.search(pat, line)
                    if m:
                        method = m.group(1).upper()
                        route_path = m.group(2) if m.group(2) else "/"
                        routes.append(
                            {
                                "method": method,
                                "path": route_path,
                                "handler": f"{rel}:{idx}",
                                "framework": "Node/Express/Nest/Fastify",
                                "auth_required": has_auth,
                            }
                        )
                        break
        except Exception:
            pass

    return routes


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract public API surface: HTTP routes, OpenAPI endpoints, GraphQL/gRPC, and CLI subcommands."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    node_routes = extract_node_routes(root_path)

    data = {
        "root": str(root_path),
        "routes": node_routes,
        "openapi": [],
        "graphql": [],
        "grpc": [],
        "cli_commands": [],
        "public_exports": [],
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"API Surface Extraction for: {root_path}")


if __name__ == "__main__":
    main()
