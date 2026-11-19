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
    r"""(?:app|router|fastify|server)\.(get|post|put|delete|patch|options|head)\s*\(\s*['"`]([^'"`]+)['"`]""",
    # @Get('/path') in NestJS
    r"""@(Get|Post|Put|Delete|Patch)\s*\(\s*['"`]?([^'"`]*)['"`]?\s*\)""",
]


def extract_node_routes(root_path: Path):
    """Extract HTTP method, path, and file:line handler citations from Node/TS files."""
    root_path = root_path.resolve()
    routes = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (".js", ".ts", ".mjs", ".cjs", ".jsx", ".tsx", ".mts", ".cts"):
            continue

        rel = str(file_path.relative_to(root_path))
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines, start=1):
                # Check for auth tokens on current line or preceding decorator lines
                auth_tokens = [
                    "authenticate",
                    "requireAuth",
                    "authMiddleware",
                    "passport",
                    "verifyToken",
                    "jwt",
                    "@UseGuards",
                    "checkAuth",
                ]
                combined = line
                # Look ahead up to 4 lines if method call spans multiple lines
                if re.search(r"""(?:app|router|fastify|server)\.(?:get|post|put|delete|patch|options|head)\s*\(""", line):
                    combined = " ".join(l.strip() for l in lines[idx - 1 : min(len(lines), idx + 4)])

                has_auth = any(tok in combined for tok in auth_tokens)
                if not has_auth and idx > 1:
                    prev_line = lines[idx - 2].strip()
                    if prev_line.startswith("@") and any(tok in prev_line for tok in auth_tokens):
                        has_auth = True

                for pat in NODE_ROUTE_PATTERNS:
                    m = re.search(pat, combined)
                    if m:
                        method = m.group(1).upper()
                        route_path = m.group(2) if m.group(2) else "/"
                        # Ignore non-path patterns (e.g. variable identifiers without slash)
                        if not route_path.startswith("/") and not route_path.startswith("*"):
                            continue
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
                    combined_py = line
                    if line.strip().startswith("@"):
                        combined_py = " ".join(l.strip() for l in lines[idx - 1 : min(len(lines), idx + 4)])

                    # FastAPI: @app.get('/path')
                    m_fastapi = re.search(
                        r"""@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]""",
                        combined_py,
                    )
                    if m_fastapi:
                        routes.append(
                            {
                                "method": m_fastapi.group(1).upper(),
                                "path": m_fastapi.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "FastAPI",
                                "auth_required": any(tok in combined_py for tok in ["login_required", "Depends(", "Security(", "OAuth2", "HTTPBearer"]),
                            }
                        )
                        continue

                    # Flask: @app.route('/path', methods=['GET', 'POST']) or @bp.route(...)
                    m_flask = re.search(r"""@(?:[a-zA-Z0-9_]+)\.route\s*\(\s*['"`]([^'"`]+)['"`](?:.*?methods\s*=\s*\[(.*?)\])?""", combined_py)
                    if m_flask:
                        route_path = m_flask.group(1)
                        methods_raw = m_flask.group(2)
                        if methods_raw:
                            methods_list = [m.strip("'\" ") for m in methods_raw.split(",") if m.strip("'\" ")]
                            method_str = "/".join(methods_list).upper() if methods_list else "GET"
                        else:
                            method_str = "GET"
                        has_flask_auth = any(
                            tok in combined_py
                            for tok in ["login_required", "jwt_required", "token_required", "requires_auth", "permission_required", "auth_required"]
                        )
                        routes.append(
                            {
                                "method": method_str,
                                "path": route_path,
                                "handler": f"{rel}:{idx}",
                                "framework": "Flask",
                                "auth_required": has_flask_auth,
                            }
                        )
                        continue

                    # Django: path('users/', views.user_list) or re_path(r'^users/', ...)
                    m_django = re.search(r"""(?:path|re_path)\s*\(\s*r?['"]([^'"]+)['"]""", line)
                    if m_django and "urls" in name:
                        clean_p = m_django.group(1).lstrip("^/").rstrip("$")
                        routes.append(
                            {
                                "method": "ANY",
                                "path": f"/{clean_p}",
                                "handler": f"{rel}:{idx}",
                                "framework": "Django",
                                "auth_required": False,
                            }
                        )
                        continue

                    # Django REST Framework router.register('users', UserViewSet)
                    m_drf = re.search(r"""router\.register\s*\(\s*r?['"]([^'"]+)['"]""", line)
                    if m_drf:
                        routes.append(
                            {
                                "method": "CRUD",
                                "path": f"/{m_drf.group(1).strip('/')}",
                                "handler": f"{rel}:{idx}",
                                "framework": "Django/DRF",
                                "auth_required": False,
                            }
                        )
                        continue

                # 2. Go (Gin, Echo, Chi, net/http): r.GET('/path', handler) or r.Get('/path', handler)
                elif ext == ".go":
                    m_go = re.search(
                        r"""(?:r|router|app|g|api)\.(GET|POST|PUT|DELETE|PATCH|Get|Post|Put|Delete|Patch)\s*\(\s*['"]([^'"]+)['"]""",
                        line,
                    )
                    if m_go:
                        routes.append(
                            {
                                "method": m_go.group(1).upper(),
                                "path": m_go.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "Go/Gin/Echo/Chi",
                                "auth_required": False,
                            }
                        )
                        continue

                    m_http = re.search(
                        r"""(?:http|mux|router|r|srv)\.HandleFunc\s*\(\s*['"]([^'"]+)['"]""",
                        line,
                    )
                    if m_http:
                        routes.append(
                            {
                                "method": "ANY",
                                "path": m_http.group(1),
                                "handler": f"{rel}:{idx}",
                                "framework": "Go/net-http",
                                "auth_required": False,
                            }
                        )
                        continue

                # 3. Java/Kotlin (Spring): @GetMapping('/path') or @RequestMapping
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

                    m_req_map = re.search(
                        r"""@RequestMapping\s*\(\s*(?:(?:value|path)\s*=\s*)?['"]?([^'",)]*)['"]?(?:.*method\s*=\s*(?:RequestMethod\.)?([A-Z]+))?""",
                        line,
                    )
                    if m_req_map:
                        routes.append(
                            {
                                "method": m_req_map.group(2) or "ANY",
                                "path": m_req_map.group(1) or "/",
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

                # 5. Rust (Actix-web / Axum)
                elif ext == ".rs":
                    m_actix = re.search(r"""#\[(get|post|put|delete|patch)\s*\(\s*["']([^"']+)["']\s*\)\]""", line, re.IGNORECASE)
                    if m_actix:
                        routes.append(
                            {
                                "method": m_actix.group(1).upper(),
                                "path": m_actix.group(2),
                                "handler": f"{rel}:{idx}",
                                "framework": "Rust/Actix",
                                "auth_required": False,
                            }
                        )
                        continue
                    m_axum = re.search(r"""\.route\s*\(\s*["']([^"']+)["']\s*,\s*(get|post|put|delete|patch)\s*\(""", line, re.IGNORECASE)
                    if m_axum:
                        routes.append(
                            {
                                "method": m_axum.group(2).upper(),
                                "path": m_axum.group(1),
                                "handler": f"{rel}:{idx}",
                                "framework": "Rust/Axum",
                                "auth_required": False,
                            }
                        )
                        continue
        except Exception:
            pass

    return routes


def extract_openapi_specs(root_path: Path):
    """Parse OpenAPI/Swagger specifications from JSON and YAML files using stdlib."""
    root_path = root_path.resolve()
    endpoints = []
    import json

    openapi_names = {
        "openapi.json",
        "openapi.yaml",
        "openapi.yml",
        "swagger.json",
        "swagger.yaml",
        "swagger.yml",
    }

    for file_path in _common.walk_repo(root_path):
        name = file_path.name.lower()
        if name in openapi_names:
            rel = str(file_path.relative_to(root_path))
            try:
                if name.endswith(".json"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        doc = json.load(f)
                    paths = doc.get("paths", {})
                    for ep_path, methods in paths.items():
                        if isinstance(methods, dict):
                            for m, mdata in methods.items():
                                if m.lower() in ("get", "post", "put", "delete", "patch", "options"):
                                    summary = mdata.get("summary", "") if isinstance(mdata, dict) else ""
                                    endpoints.append(
                                        {
                                            "spec_file": rel,
                                            "path": ep_path,
                                            "method": m.upper(),
                                            "summary": summary,
                                        }
                                    )
                else:
                    # YAML parsing with indentation tracking
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    curr_path = None
                    curr_path_indent = -1
                    for line in content.splitlines():
                        if not line.strip() or line.strip().startswith("#"):
                            continue
                        m_path = re.match(r"""^(\s*)(?:['"]?)(/[a-zA-Z0-9_{}/.-]+)(?:['"]?):\s*$""", line)
                        if m_path:
                            curr_path_indent = len(m_path.group(1))
                            curr_path = m_path.group(2)
                            continue
                        if curr_path:
                            m_method = re.match(r"""^(\s+)(get|post|put|delete|patch|options|head):\s*$""", line, re.IGNORECASE)
                            if m_method and len(m_method.group(1)) > curr_path_indent:
                                endpoints.append(
                                    {
                                        "spec_file": rel,
                                        "path": curr_path,
                                        "method": m_method.group(2).upper(),
                                        "summary": "",
                                    }
                                )
                            elif len(line) - len(line.lstrip()) <= curr_path_indent:
                                curr_path = None
            except Exception:
                pass

    return endpoints


def extract_schemas_and_rpc(root_path: Path):
    """Extract GraphQL queries/mutations, gRPC services, and tRPC routers."""
    root_path = root_path.resolve()
    graphql_ops = []
    grpc_services = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        rel = str(file_path.relative_to(root_path))

        # 1. GraphQL (.graphql, .gql)
        if ext in (".graphql", ".gql"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                # Find queries and mutations (including extend type)
                for m in re.finditer(r"(?:(?:extend\s+)?type\s+(Query|Mutation|Subscription)\s*\{([^}]+)\})", content):
                    op_type = m.group(1)
                    body = m.group(2)
                    for line in body.splitlines():
                        field_m = re.match(r"\s*([a-zA-Z0-9_]+)\s*(\(.*?\))?\s*:\s*([a-zA-Z0-9_!\[\]]+)", line)
                        if field_m:
                            field_name = field_m.group(1)
                            return_type = field_m.group(3)
                            graphql_ops.append(
                                {
                                    "file": rel,
                                    "operation": op_type,
                                    "name": field_name,
                                    "return_type": return_type,
                                }
                            )
            except Exception:
                pass

        # 2. gRPC (.proto)
        elif ext == ".proto":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for s_match in re.finditer(r"service\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}", content):
                    service_name = s_match.group(1)
                    body = s_match.group(2)
                    for rpc_m in re.finditer(
                        r"rpc\s+([a-zA-Z0-9_]+)\s*\(\s*(?:stream\s+)?([a-zA-Z0-9_.]+)\s*\)\s*returns\s*\(\s*(?:stream\s+)?([a-zA-Z0-9_.]+)\s*\)",
                        body,
                    ):
                        rpc_name = rpc_m.group(1)
                        req_type = rpc_m.group(2)
                        res_type = rpc_m.group(3)
                        grpc_services.append(
                            {
                                "file": rel,
                                "service": service_name,
                                "rpc": rpc_name,
                                "request": req_type,
                                "response": res_type,
                            }
                        )
            except Exception:
                pass

        # 3. tRPC (.ts/.js)
        elif ext in (".ts", ".js"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        if "publicProcedure" in line or "createTRPCRouter" in line or "router({" in line:
                            trpc_m = re.search(r"([a-zA-Z0-9_]+)\s*:\s*(?:publicProcedure|procedure)\.(query|mutation)", line)
                            if trpc_m:
                                graphql_ops.append(
                                    {
                                        "file": f"{rel}:{idx}",
                                        "operation": f"tRPC-{trpc_m.group(2).upper()}",
                                        "name": trpc_m.group(1),
                                        "return_type": "inferred",
                                    }
                                )
            except Exception:
                pass

    return graphql_ops, grpc_services


def extract_cli_and_exports(root_path: Path):
    """Extract CLI subcommands and library public exports (__all__, index exports)."""
    root_path = root_path.resolve()
    cli_commands = []
    public_exports = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()
        ext = file_path.suffix.lower()

        # 1. CLI subcommands
        if ext in (".py", ".js", ".ts", ".go", ".rs"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        # Commander: .command('foo')
                        m_cmd = re.search(r"""\.command\s*\(\s*['"]([^'"]+)['"]""", line)
                        if m_cmd:
                            cli_commands.append({"file": f"{rel}:{idx}", "command": m_cmd.group(1)})
                        # Click / Typer: @cli.command('foo') or @app.command()
                        m_click = re.search(r"""@(?:cli|app)\.command\s*\(\s*(?:['"]([^'"]+)['"])?""", line)
                        if m_click:
                            cmd_name = m_click.group(1) or "inferred"
                            cli_commands.append({"file": f"{rel}:{idx}", "command": cmd_name})
                        # Cobra: Use: "foo"
                        m_cobra = re.search(r"""Use:\s*["']([^"'\s]+)""", line)
                        if m_cobra and ext == ".go":
                            cli_commands.append({"file": f"{rel}:{idx}", "command": m_cobra.group(1)})
                        # Python argparse: add_parser("build")
                        m_argp = re.search(r"""add_parser\s*\(\s*['"]([^'"]+)['"]""", line)
                        if m_argp and ext == ".py":
                            cli_commands.append({"file": f"{rel}:{idx}", "command": m_argp.group(1)})
            except Exception:
                pass

        # 2. Public library exports (__all__ or index.ts/js exports)
        if name in ("__init__.py", "index.ts", "index.js", "mod.rs", "lib.rs"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if ext == ".py":
                    # __all__ = ["foo", "bar"]
                    m_all = re.search(r"""__all__\s*=\s*\[([^\]]+)\]""", content, re.DOTALL)
                    if m_all:
                        items = re.findall(r"""['"]([^'"]+)['"]""", m_all.group(1))
                        for item in items:
                            public_exports.append({"file": rel, "export": item, "type": "Python __all__"})
                elif ext in (".ts", ".js"):
                    # export { a, b } or export const a or export function b
                    for line in content.splitlines():
                        if line.strip().startswith("export "):
                            m_exp = re.search(r"""export\s+(?:const|function|class|type|interface)\s+([a-zA-Z0-9_]+)""", line)
                            if m_exp:
                                public_exports.append({"file": rel, "export": m_exp.group(1), "type": "Named export"})
                            m_named = re.search(r"""export\s*\{([^}]+)\}""", line)
                            if m_named:
                                for token in m_named.group(1).split(","):
                                    clean_tok = token.strip().split(" as ")[0].strip()
                                    if clean_tok:
                                        public_exports.append({"file": rel, "export": clean_tok, "type": "Named export"})
            except Exception:
                pass

    return cli_commands, public_exports


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
    openapi_endpoints = extract_openapi_specs(root_path)
    graphql_ops, grpc_services = extract_schemas_and_rpc(root_path)
    cli_commands, public_exports = extract_cli_and_exports(root_path)

    data = {
        "root": str(root_path),
        "routes": all_routes,
        "openapi": openapi_endpoints,
        "graphql": graphql_ops,
        "grpc": grpc_services,
        "cli_commands": cli_commands,
        "public_exports": public_exports,
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"API Surface Extraction for: {root_path}")
        print(f"\nHTTP Routes Discovered ({len(all_routes)}):")
        print(f"{'Method':<10} {'Path':<30} {'Auth':<6} {'Handler':<30}")
        print("-" * 78)
        for r in all_routes[:25]:
            auth = "yes" if r["auth_required"] else "no"
            print(f"{r['method']:<10} {r['path']:<30} {auth:<6} {r['handler']:<30}")
        if len(all_routes) > 25:
            print(f"  ... and {len(all_routes) - 25} more routes")

        if openapi_endpoints:
            print(f"\nOpenAPI Endpoints Discovered ({len(openapi_endpoints)}):")
            for ep in openapi_endpoints[:10]:
                print(f"  [{ep['method']}] {ep['path']} ({ep['spec_file']})")

        if graphql_ops:
            print(f"\nGraphQL / tRPC Operations Discovered ({len(graphql_ops)}):")
            for op in graphql_ops[:10]:
                print(f"  [{op['operation']}] {op['name']} -> {op['return_type']} ({op['file']})")

        if grpc_services:
            print(f"\ngRPC Services Discovered ({len(grpc_services)}):")
            for s in grpc_services[:10]:
                print(f"  {s['service']}.{s['rpc']}({s['request']}) -> {s['response']} ({s['file']})")

        if cli_commands:
            print(f"\nCLI Commands Discovered ({len(cli_commands)}):")
            for c in cli_commands[:10]:
                print(f"  - {c['command']} ({c['file']})")

        if public_exports:
            print(f"\nPublic Library Exports Discovered ({len(public_exports)}):")
            for exp in public_exports[:10]:
                print(f"  - {exp['export']} [{exp['type']}] ({exp['file']})")


if __name__ == "__main__":
    main()
