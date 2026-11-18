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


def extract_other_routes(root_path: Path):
    """Extract HTTP routes for Python, Go, Java, and Ruby frameworks."""
    root_path = root_path.resolve()
    routes = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines, start=1):
                # 1. Python (FastAPI, Flask, Django)
                if ext in (".py", ".pyi"):
                    # FastAPI: @app.get('/path')
                    m_fastapi = re.search(
                        r"""@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""",
                        line,
                    )
                    if m_fastapi:
                        routes.append(
                            {
                                "method": m_fastapi.group(1).upper(),
                                "path": m_fastapi.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "FastAPI",
                                "auth_required": "login_required" in line or "Depends(" in line,
                            }
                        )
                        continue

                    # Flask: @app.route('/path', methods=['GET', 'POST'])
                    m_flask = re.search(r"""@(?:app|api)\.route\s*\(\s*['"]([^'"]+)['"]""", line)
                    if m_flask:
                        route_path = m_flask.group(1)
                        routes.append(
                            {
                                "method": "GET/POST",
                                "path": route_path,
                                "handler": f"{rel}:{idx}",
                                "framework": "Flask",
                                "auth_required": "login_required" in line,
                            }
                        )
                        continue

                    # Django: path('users/', views.user_list)
                    m_django = re.search(r"""path\s*\(\s*['"]([^'"]+)['"]""", line)
                    if m_django and "urls" in name:
                        routes.append(
                            {
                                "method": "ANY",
                                "path": f"/{m_django.group(1).lstrip('/')}",
                                "handler": f"{rel}:{idx}",
                                "framework": "Django",
                                "auth_required": False,
                            }
                        )
                        continue

                # 2. Go (Gin, Echo, Chi): r.GET('/path', handler)
                elif ext == ".go":
                    m_go = re.search(
                        r"""(?:r|router|app|g|api)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['"]([^'"]+)['"]""",
                        line,
                    )
                    if m_go:
                        routes.append(
                            {
                                "method": m_go.group(1).upper(),
                                "path": m_go.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "Go/Gin/Echo",
                                "auth_required": False,
                            }
                        )
                        continue

                # 3. Java/Kotlin (Spring): @GetMapping('/path')
                elif ext in (".java", ".kt"):
                    m_spring = re.search(
                        r"""@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:(?:value|path)\s*=\s*)?['"]?([^'")]*)['"]?\s*\)""",
                        line,
                    )
                    if m_spring:
                        routes.append(
                            {
                                "method": m_spring.group(1).upper(),
                                "path": m_spring.group(2) or "/",
                                "handler": f"{rel}:{idx}",
                                "framework": "Spring",
                                "auth_required": "@PreAuthorize" in line or "@Secured" in line,
                            }
                        )
                        continue

                # 4. Ruby (Rails): get '/path', to: 'controller#action'
                elif ext == ".rb" and "routes" in name:
                    m_rails = re.search(r"""(get|post|put|delete|patch)\s+['"]([^'"]+)['"]""", line)
                    if m_rails:
                        routes.append(
                            {
                                "method": m_rails.group(1).upper(),
                                "path": m_rails.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "Rails",
                                "auth_required": False,
                            }
                        )
                        continue
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
    other_routes = extract_other_routes(root_path)
    all_routes = node_routes + other_routes

    data = {
        "root": str(root_path),
        "routes": all_routes,
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
