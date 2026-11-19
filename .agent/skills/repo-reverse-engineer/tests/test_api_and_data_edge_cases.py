#!/usr/bin/env python3
"""Unit tests verifying edge cases in API surface extraction and data model parsing."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXTRACT_API_PY = SCRIPTS_DIR / "extract_api_surface.py"
EXTRACT_DATA_MODEL_PY = SCRIPTS_DIR / "extract_data_model.py"


class TestApiAndDataEdgeCases(unittest.TestCase):
    def test_multiline_routes_and_grpc_streaming(self):
        """Verify multiline route definitions and gRPC streaming operations."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "server.ts").write_text(
                "import express from 'express';\n"
                "const app = express();\n"
                "app.get(\n"
                "  '/api/v1/orders',\n"
                "  authenticate,\n"
                "  (req, res) => res.json([])\n"
                ");\n"
            )
            (r / "chat.proto").write_text(
                'syntax = "proto3";\n'
                'service ChatService {\n'
                '  rpc StreamChat (stream Message) returns (stream Message);\n'
                '}\n'
            )
            (r / "schema.graphql").write_text(
                "extend type Query {\n"
                "  getUser(id: ID!): User\n"
                "}\n"
            )

            cmd = ["python3", str(EXTRACT_API_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_api_surface failed: {res.stderr}")
            data = json.loads(res.stdout)

            routes = data.get("routes", [])
            order_route = next((rt for rt in routes if rt["path"] == "/api/v1/orders"), None)
            self.assertIsNotNone(order_route, "Multiline route /api/v1/orders was not extracted")
            self.assertEqual(order_route["method"], "GET")
            self.assertTrue(order_route["auth_required"])

            grpc = data.get("grpc", [])
            self.assertEqual(len(grpc), 1)
            self.assertEqual(grpc[0]["rpc"], "StreamChat")
            self.assertEqual(grpc[0]["request"], "Message")

            graphql = data.get("graphql", [])
            self.assertEqual(len(graphql), 1)
            self.assertEqual(graphql[0]["name"], "getUser")

    def test_sqlalchemy_20_and_prisma_composite_pk(self):
        """Verify SQLAlchemy 2.0 Mapped columns and Prisma @@id composite keys."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "models.py").write_text(
                "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n"
                "from sqlalchemy import ForeignKey\n"
                "class Base(DeclarativeBase): pass\n"
                "class Membership(Base):\n"
                "    __tablename__ = 'memberships'\n"
                "    id: Mapped[int] = mapped_column(primary_key=True)\n"
                "    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))\n"
            )
            (r / "schema.prisma").write_text(
                "model TeamMember {\n"
                "  teamId String\n"
                "  userId String\n"
                "  role   String\n"
                "  @@id([teamId, userId])\n"
                "}\n"
            )

            cmd = ["python3", str(EXTRACT_DATA_MODEL_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_data_model failed: {res.stderr}")
            data = json.loads(res.stdout)

            entities = {e["name"]: e for e in data.get("entities", [])}
            self.assertIn("Membership", entities)
            self.assertIn("TeamMember", entities)

            # Check SQLAlchemy PK and relation
            m_cols = {c["name"]: c for c in entities["Membership"]["columns"]}
            self.assertTrue(m_cols["id"]["primary_key"])
            relations = [(rel["from"], rel["to"]) for rel in data.get("relations", [])]
            self.assertIn(("Membership", "users"), relations)

            # Check Prisma composite PK
            tm_cols = {c["name"]: c for c in entities["TeamMember"]["columns"]}
            self.assertTrue(tm_cols["teamId"]["primary_key"], "teamId should be flagged as composite PK")
            self.assertTrue(tm_cols["userId"]["primary_key"], "userId should be flagged as composite PK")
            self.assertFalse(tm_cols["role"]["primary_key"])


if __name__ == "__main__":
    unittest.main()
