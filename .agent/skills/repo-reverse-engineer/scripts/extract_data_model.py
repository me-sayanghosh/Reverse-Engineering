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


def parse_prisma_and_orm_entities(root_path: Path):
    """Parse schema.prisma and TypeORM/Sequelize decorator-based models."""
    root_path = root_path.resolve()
    entities = {}
    relations = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        rel = str(file_path.relative_to(root_path))
        name = file_path.name.lower()
        ext = file_path.suffix.lower()

        # 1. Prisma schema
        if name == "schema.prisma" or ext == ".prisma":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"model\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}", content):
                    model_name = m.group(1)
                    body = m.group(2)
                    columns = []

                    for raw_line in body.splitlines():
                        line = raw_line.strip()
                        if not line or line.startswith("//"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            f_name = parts[0]
                            f_type = parts[1]
                            is_pk = "@id" in line

                            # Check relation: e.g. author User @relation(fields: [authorId], references: [id])
                            rel_m = re.search(r"@relation\s*\((.*?)\)", line)
                            if rel_m:
                                target_model = f_type.rstrip("?[]")
                                relations.append(
                                    {
                                        "from": model_name,
                                        "to": target_model,
                                        "from_column": f_name,
                                        "to_column": "id",
                                        "type": "prisma_relation",
                                    }
                                )

                            columns.append(
                                {
                                    "name": f_name,
                                    "type": f_type,
                                    "primary_key": is_pk,
                                }
                            )

                    entities[model_name] = {
                        "name": model_name,
                        "file": rel,
                        "columns": columns,
                        "source": "Prisma",
                    }
            except Exception:
                pass

        # 2. TypeORM decorators (@Entity, @Column, @ManyToOne, etc.)
        elif ext in (".ts", ".js"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "@Entity" in content:
                    m_entity = re.search(r"@Entity\s*\([^\)]*\)\s*(?:export\s+)?class\s+([a-zA-Z0-9_]+)", content)
                    if m_entity:
                        entity_name = m_entity.group(1)
                        columns = []
                        # Detect columns
                        for col_m in re.finditer(r"@(Column|PrimaryGeneratedColumn)\s*\([^\)]*\)\s*([a-zA-Z0-9_]+)(?:\s*[:=]\s*([a-zA-Z0-9_]+))?", content):
                            col_type = col_m.group(3) or "any"
                            is_pk = col_m.group(1) == "PrimaryGeneratedColumn"
                            columns.append({"name": col_m.group(2), "type": col_type, "primary_key": is_pk})

                        # Detect relations
                        for rel_m in re.finditer(r"@(ManyToOne|OneToMany|OneToOne|ManyToMany)\s*\(\s*\(\)\s*=>\s*([a-zA-Z0-9_]+)", content):
                            target_entity = rel_m.group(2)
                            relations.append({
                                "from": entity_name,
                                "to": target_entity,
                                "type": rel_m.group(1),
                            })

                        entities[entity_name] = {
                            "name": entity_name,
                            "file": rel,
                            "columns": columns,
                            "source": "TypeORM",
                        }
            except Exception:
                pass

    return list(entities.values()), relations


def parse_mongoose_schemas(root_path: Path):
    """Parse Mongoose new Schema({...}) declarations, fields, and ref relations."""
    root_path = root_path.resolve()
    entities = {}
    relations = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        if ext not in (".js", ".ts", ".mjs"):
            continue

        rel = str(file_path.relative_to(root_path))
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if "Schema(" in content:
                # Find model name if declared: mongoose.model('User', ...)
                m_model = re.search(r"""mongoose\.model\s*\(\s*['"]([a-zA-Z0-9_]+)['"]""", content)
                model_name = m_model.group(1) if m_model else file_path.stem

                # Find Schema body using balanced brace matching
                schema_idx = content.find("Schema(")
                brace_start = content.find("{", schema_idx) if schema_idx != -1 else -1
                if brace_start != -1:
                    depth = 0
                    brace_end = -1
                    for i in range(brace_start, len(content)):
                        if content[i] == "{":
                            depth += 1
                        elif content[i] == "}":
                            depth -= 1
                            if depth == 0:
                                brace_end = i
                                break

                    if brace_end != -1:
                        body = content[brace_start + 1 : brace_end]
                        columns = []
                        # Parse field declarations line by line or pattern
                        for line in body.splitlines():
                            line = line.strip().rstrip(",")
                            if not line or line.startswith("//"):
                                continue
                            f_match = re.match(r"""['"]?([a-zA-Z0-9_]+)['"]?\s*:\s*(.*)""", line)
                            if f_match:
                                f_name = f_match.group(1)
                                f_def = f_match.group(2)

                                # Extract ref: e.g. { type: Schema.Types.ObjectId, ref: 'User' }
                                ref_m = re.search(r"""ref\s*:\s*['"]([a-zA-Z0-9_]+)['"]""", f_def)
                                if ref_m:
                                    target_ref = ref_m.group(1)
                                    relations.append(
                                        {
                                            "from": model_name,
                                            "to": target_ref,
                                            "from_column": f_name,
                                            "type": "mongoose_ref",
                                        }
                                    )

                                # Extract type
                                type_m = re.search(r"""type\s*:\s*([a-zA-Z0-9_.]+)""", f_def)
                                col_type = type_m.group(1) if type_m else f_def.split()[0].rstrip(",{}")
                                columns.append(
                                    {
                                        "name": f_name,
                                        "type": col_type,
                                        "primary_key": f_name in ("_id", "id"),
                                    }
                                )

                        entities[model_name] = {
                            "name": model_name,
                            "file": rel,
                            "columns": columns,
                            "source": "Mongoose",
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
    prisma_entities, prisma_relations = parse_prisma_and_orm_entities(root_path)
    mongoose_entities, mongoose_relations = parse_mongoose_schemas(root_path)

    all_entities = sql_entities + prisma_entities + mongoose_entities
    all_relations = sql_relations + prisma_relations + mongoose_relations

    data = {
        "root": str(root_path),
        "entities": all_entities,
        "relations": all_relations,
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print("erDiagram\n  ENTITY ||--o{ OTHER : has")
    else:
        print(f"Data Model Extraction for: {root_path}")


if __name__ == "__main__":
    main()
