#!/usr/bin/env python3
"""Unit tests verifying SQLModel, Beanie Document, and unquoted ForeignKey parsing in extract_data_model."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
EXTRACT_DATA_MODEL_PY = SCRIPTS_DIR / "extract_data_model.py"


class TestDataModelSqlmodelAndRelations(unittest.TestCase):
    def test_sqlmodel_and_document_parsing(self):
        """Verify SQLModel models and Beanie Document models are extracted with relations."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "models.py").write_text(
                "from sqlmodel import SQLModel, Field\n"
                "from beanie import Document\n"
                "class Hero(SQLModel, table=True):\n"
                "    id: int = Field(primary_key=True)\n"
                "    name: str\n"
                "    team_id: int = Field(foreign_key=\"team.id\")\n"
                "class UserProfile(Document):\n"
                "    email: str\n"
            )

            cmd = ["python3", str(EXTRACT_DATA_MODEL_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_data_model failed: {res.stderr}")
            data = json.loads(res.stdout)

            entities = {e["name"]: e for e in data.get("entities", [])}
            self.assertIn("Hero", entities, "SQLModel entity Hero was not extracted")
            self.assertEqual(entities["Hero"]["source"], "SQLModel")
            self.assertIn("UserProfile", entities, "Beanie Document UserProfile was not extracted")
            self.assertEqual(entities["UserProfile"]["source"], "Document/Beanie")

            relations = [(rel["from"], rel["to"]) for rel in data.get("relations", [])]
            self.assertIn(("Hero", "team"), relations, "Foreign key from Hero to team was not captured")

    def test_composite_primary_key_in_sql(self):
        """Verify table-level PRIMARY KEY (a, b) flags both columns as primary keys."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td).resolve()
            (r / "001_init.sql").write_text(
                "CREATE TABLE user_roles (\n"
                "    user_id INT NOT NULL,\n"
                "    role_id INT NOT NULL,\n"
                "    PRIMARY KEY (user_id, role_id)\n"
                ");\n"
            )

            cmd = ["python3", str(EXTRACT_DATA_MODEL_PY), str(r), "--json"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(res.returncode, 0, f"extract_data_model failed: {res.stderr}")
            data = json.loads(res.stdout)

            entities = {e["name"]: e for e in data.get("entities", [])}
            self.assertIn("user_roles", entities)
            cols = {c["name"]: c["primary_key"] for c in entities["user_roles"]["columns"]}
            self.assertTrue(cols.get("user_id"), "user_id was not flagged as PK")
            self.assertTrue(cols.get("role_id"), "role_id was not flagged as PK")


if __name__ == "__main__":
    unittest.main()
