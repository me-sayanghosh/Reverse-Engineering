#!/usr/bin/env python3
"""Tests for Peewee ORM models, composite foreign keys in SQL migrations, and SQLAlchemy 2.0 relations."""

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import extract_data_model


class TestPeeweeAndCompositeFk(unittest.TestCase):
    def test_composite_foreign_key_in_sql(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            migration = tmp / "migrations" / "001_create_tables.sql"
            migration.parent.mkdir(parents=True)
            migration.write_text(
                """
CREATE TABLE orders (
    tenant_id INT,
    order_id INT,
    total DECIMAL(10, 2),
    PRIMARY KEY (tenant_id, order_id)
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    tenant_id INT,
    order_id INT,
    product_name VARCHAR(100),
    CONSTRAINT fk_order_tenant FOREIGN KEY (tenant_id, order_id) REFERENCES orders (tenant_id, order_id)
);
""",
                encoding="utf-8",
            )

            entities, relations = extract_data_model.parse_sql_migrations(tmp)
            entity_names = {e["name"] for e in entities}
            self.assertIn("orders", entity_names)
            self.assertIn("order_items", entity_names)

            orders_ent = next(e for e in entities if e["name"] == "orders")
            order_pks = [c["name"] for c in orders_ent["columns"] if c["primary_key"]]
            self.assertIn("tenant_id", order_pks)
            self.assertIn("order_id", order_pks)

            # Check composite foreign key relation
            composite_rel = next((r for r in relations if r["from"] == "order_items" and r["to"] == "orders"), None)
            self.assertIsNotNone(composite_rel)
            self.assertIn("tenant_id", composite_rel["from_column"])
            self.assertIn("order_id", composite_rel["from_column"])

    def test_peewee_model_extraction(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            models_py = tmp / "models.py"
            models_py.write_text(
                """
from peewee import Model, CharField, TextField, ForeignKeyField, SqliteDatabase

db = SqliteDatabase(':memory:')

class Author(Model):
    name = CharField()
    class Meta:
        database = db

class Book(Model):
    author = ForeignKeyField(Author, backref='books')
    title = CharField()
    class Meta:
        database = db
""",
                encoding="utf-8",
            )

            entities, relations = extract_data_model.parse_python_models(tmp)
            entity_names = {e["name"] for e in entities}
            self.assertIn("Author", entity_names)
            self.assertIn("Book", entity_names)

            # Check foreign key relation from Book to Author
            fk_rel = next((r for r in relations if r["from"] == "Book" and r["to"] == "Author"), None)
            self.assertIsNotNone(fk_rel)
            self.assertEqual(fk_rel["from_column"], "author")

    def test_sqlalchemy2_type_annotated_relationship(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            sa_models = tmp / "models.py"
            sa_models.write_text(
                """
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Department(Base):
    __tablename__ = 'departments'
    id: Mapped[int] = mapped_column(primary_key=True)
    employees: Mapped[list[Employee]] = relationship()

class Employee(Base):
    __tablename__ = 'employees'
    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
""",
                encoding="utf-8",
            )

            entities, relations = extract_data_model.parse_python_models(tmp)
            rel_dept = next((r for r in relations if r["from"] == "Department" and r["to"] == "Employee"), None)
            self.assertIsNotNone(rel_dept)


if __name__ == "__main__":
    unittest.main()
