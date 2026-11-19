#!/usr/bin/env python3
"""Tests for Next.js App Router, Go Echo/Fiber, and Rust Rocket/Axum route extraction."""

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import extract_api_surface


class TestNextJsRoutesAndEcho(unittest.TestCase):
    def test_nextjs_app_router_handlers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            users_route = tmp / "src" / "app" / "api" / "users" / "route.ts"
            users_route.parent.mkdir(parents=True)
            users_route.write_text(
                """
export async function GET(request: Request) {
    const session = await getServerSession();
    return Response.json({ users: [] });
}

export async function POST(request: Request) {
    return Response.json({ success: true });
}
""",
                encoding="utf-8",
            )

            root_route = tmp / "src" / "app" / "route.ts"
            root_route.write_text(
                """
export function GET() {
    return new Response('OK');
}
""",
                encoding="utf-8",
            )

            routes = extract_api_surface.extract_node_routes(tmp)
            paths = {r["path"] for r in routes}
            methods = {(r["method"], r["path"]) for r in routes}

            self.assertIn("/api/users", paths)
            self.assertIn("/", paths)
            self.assertIn(("GET", "/api/users"), methods)
            self.assertIn(("POST", "/api/users"), methods)
            self.assertIn(("GET", "/"), methods)

            # Check auth_required detection from getServerSession
            get_users_route = next(r for r in routes if r["path"] == "/api/users" and r["method"] == "GET")
            self.assertTrue(get_users_route["auth_required"])

    def test_go_echo_and_fiber_routes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            main_go = tmp / "main.go"
            main_go.write_text(
                """package main

func main() {
    e := echo.New()
    e.GET("/api/v1/health", HealthCheck)
    e.POST("/api/v1/login", Login)

    app := fiber.New()
    app.Get("/metrics", MetricsHandler)
}
""",
                encoding="utf-8",
            )

            routes = extract_api_surface.extract_other_routes(tmp)
            endpoints = {(r["method"], r["path"]) for r in routes}
            self.assertIn(("GET", "/api/v1/health"), endpoints)
            self.assertIn(("POST", "/api/v1/login"), endpoints)
            self.assertIn(("GET", "/metrics"), endpoints)

    def test_rust_rocket_and_axum_routes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            main_rs = tmp / "src" / "main.rs"
            main_rs.parent.mkdir(parents=True)
            main_rs.write_text(
                """
#[get("/healthz")]
fn health() -> &'static str { "ok" }

fn router() -> Router {
    Router::new()
        .nest("/api", api_routes())
        .route("/items", get(list_items).post(create_item))
}
""",
                encoding="utf-8",
            )

            routes = extract_api_surface.extract_other_routes(tmp)
            endpoints = {(r["method"], r["path"]) for r in routes}
            self.assertIn(("GET", "/healthz"), endpoints)
            self.assertIn(("NEST", "/api"), endpoints)
            self.assertIn(("GET", "/items"), endpoints)


if __name__ == "__main__":
    unittest.main()
