#!/usr/bin/env python3
"""Unit tests for extract_data_model.py script."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
EXTRACT_DATA_MODEL_PY = SKILL_DIR / "scripts" / "extract_data_model.py"


class TestExtractDataModel(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # 1. SQL migration
        (self.root / "init.sql").write_text(
            "CREATE TABLE customers (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    name VARCHAR(100)\n"
            ");\n"
            "CREATE TABLE invoices (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    customer_id INT REFERENCES customers(id),\n"
            "    amount NUMERIC\n"
            ");\n"
        )

        # 2. Prisma schema
        (self.root / "schema.prisma").write_text(
            "model Account {\n"
            "  id String @id\n"
            "  balance Float\n"
            "}\n"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_data_model_json(self):
        cmd = ["python3", str(EXTRACT_DATA_MODEL_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"Script failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("entities", data)
        self.assertIn("relations", data)

        entities = data["entities"]
        names = {e["name"] for e in entities}
        self.assertIn("customers", names)
        self.assertIn("invoices", names)
        self.assertIn("Account", names)

        # Check relation
        relations = data["relations"]
        self.assertGreaterEqual(len(relations), 1)
        rel_pairs = [(r["from"], r["to"]) for r in relations]
        self.assertIn(("invoices", "customers"), rel_pairs)

    def test_extract_data_model_mermaid(self):
        cmd = ["python3", str(EXTRACT_DATA_MODEL_PY), str(self.root), "--mermaid"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertTrue(res.stdout.startswith("erDiagram"))
        self.assertIn("customers", res.stdout)
        self.assertIn("invoices", res.stdout)


if __name__ == "__main__":
    unittest.main()
