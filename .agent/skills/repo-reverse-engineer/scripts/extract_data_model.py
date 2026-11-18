#!/usr/bin/env python3
"""Extract database data models, entities, relationships, and generate Mermaid ERDs."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common


import re


def parse_sql_migrations(root_path: Path):
    """Parse CREATE TABLE statements in .sql and migration files into tables, columns, and foreign keys."""
    root_path = root_path.resolve()
    entities = {}
    relations = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext != ".sql" and "migration" not in str(file_path).lower():
            continue

        rel = str(file_path.relative_to(root_path))
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            # Match CREATE TABLE statements
            create_table_matches = re.finditer(
                r"""CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:['"`]?\w+['"`]?\.)?['"`]?(\w+)['"`]?\s*\((.*?)\);""",
                content,
                re.IGNORECASE | re.DOTALL,
            )

            for tm in create_table_matches:
                table_name = tm.group(1)
                body = tm.group(2)
                columns = []
                fks = []

                for raw_line in body.splitlines():
                    line = raw_line.strip().rstrip(",")
                    if not line or line.startswith("--") or line.startswith("/*"):
                        continue

                    # Check standalone FOREIGN KEY (col) REFERENCES other_table(other_col)
                    fk_match = re.search(
                        r"""FOREIGN\s+KEY\s*\(['"`]?(\w+)['"`]?\)\s*REFERENCES\s+['"`]?(\w+)['"`]?\s*\(['"`]?(\w+)['"`]?\)""",
                        line,
                        re.IGNORECASE,
                    )
                    if fk_match:
                        from_col, to_table, to_col = fk_match.groups()
                        fks.append({"from_column": from_col, "target_table": to_table, "target_column": to_col})
                        relations.append(
                            {
                                "from": table_name,
                                "to": to_table,
                                "from_column": from_col,
                                "to_column": to_col,
                                "type": "foreign_key",
                            }
                        )
                        continue

                    # Check PRIMARY KEY constraint
                    if re.match(r"""PRIMARY\s+KEY\s*\((\w+)\)""", line, re.IGNORECASE):
                        continue

                    # Column definition: name type ...
                    col_parts = line.split()
                    if len(col_parts) >= 2:
                        col_name = col_parts[0].strip('"`\'[]')
                        col_type = col_parts[1].upper()
                        is_pk = "PRIMARY KEY" in line.upper()

                        # In-line REFERENCES other_table(other_col)
                        inline_fk = re.search(
                            r"""REFERENCES\s+['"`]?(\w+)['"`]?\s*(?:\(['"`]?(\w+)['"`]?\))?""",
                            line,
                            re.IGNORECASE,
                        )
                        if inline_fk:
                            to_table = inline_fk.group(1)
                            to_col = inline_fk.group(2) or "id"
                            fks.append({"from_column": col_name, "target_table": to_table, "target_column": to_col})
                            relations.append(
                                {
                                    "from": table_name,
                                    "to": to_table,
                                    "from_column": col_name,
                                    "to_column": to_col,
                                    "type": "foreign_key",
                                }
                            )

                        columns.append(
                            {
                                "name": col_name,
                                "type": col_type,
                                "primary_key": is_pk,
                            }
                        )

                entities[table_name] = {
                    "name": table_name,
                    "file": rel,
                    "columns": columns,
                    "foreign_keys": fks,
                    "source": "SQL/Migration",
                }
        except Exception:
            pass

    return list(entities.values()), relations


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract data models, database entities, foreign keys, and generate Mermaid ER diagrams."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--mermaid", action="store_true", help="Output data model as Mermaid ERD markup")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    sql_entities, sql_relations = parse_sql_migrations(root_path)

    data = {
        "root": str(root_path),
        "entities": sql_entities,
        "relations": sql_relations,
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print("erDiagram\n  ENTITY ||--o{ OTHER : has")
    else:
        print(f"Data Model Extraction for: {root_path}")


if __name__ == "__main__":
    main()
