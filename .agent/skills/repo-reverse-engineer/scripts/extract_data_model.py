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
            # Match CREATE TABLE statements with depth-balanced parentheses to support nested constraints and types
            create_table_start_pattern = re.compile(
                r"""CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:['"`]?\w+['"`]?\.)?['"`]?(\w+)['"`]?\s*\(""",
                re.IGNORECASE,
            )

            for tm in create_table_start_pattern.finditer(content):
                table_name = tm.group(1)
                start_idx = tm.end()
                depth = 1
                i = start_idx
                while i < len(content) and depth > 0:
                    if content[i] == "(":
                        depth += 1
                    elif content[i] == ")":
                        depth -= 1
                    i += 1
                if depth != 0:
                    continue
                body = content[start_idx : i - 1]
                columns = []
                fks = []

                # Extract standalone or CONSTRAINT foreign key definitions across body (supporting composite keys)
                table_fks = re.finditer(
                    r"""(?:CONSTRAINT\s+['"`]?\w+['"`]?\s+)?FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+['"`]?(\w+)['"`]?\s*(?:\(([^)]+)\))?""",
                    body,
                    re.IGNORECASE,
                )
                for fkm in table_fks:
                    from_cols = [c.strip().strip('"`\' ') for c in fkm.group(1).split(",") if c.strip()]
                    to_table = fkm.group(2)
                    raw_to_cols = fkm.group(3)
                    to_cols = [c.strip().strip('"`\' ') for c in raw_to_cols.split(",") if c.strip()] if raw_to_cols else ["id"]
                    from_col = from_cols[0] if len(from_cols) == 1 else ", ".join(from_cols)
                    to_col = to_cols[0] if len(to_cols) == 1 else ", ".join(to_cols)
                    fk_obj = {"from_column": from_col, "target_table": to_table, "target_column": to_col}
                    if fk_obj not in fks:
                        fks.append(fk_obj)
                        relations.append(
                            {
                                "from": table_name,
                                "to": to_table,
                                "from_column": from_col,
                                "to_column": to_col,
                                "type": "foreign_key",
                            }
                        )

                # Extract table-level primary key definitions: PRIMARY KEY (col1, col2)
                table_pk_match = re.search(r"""(?:CONSTRAINT\s+['"`]?\w+['"`]?\s+)?PRIMARY\s+KEY\s*\(([^)]+)\)""", body, re.IGNORECASE)
                table_pks = set()
                if table_pk_match:
                    for raw_col in table_pk_match.group(1).split(","):
                        clean_col = raw_col.strip().strip('"`\'[] ')
                        if clean_col:
                            table_pks.add(clean_col)

                for raw_line in body.splitlines():
                    line = raw_line.strip().rstrip(",")
                    if not line or line.startswith("--") or line.startswith("/*"):
                        continue

                    # Skip constraint lines already parsed above
                    col_parts = line.split()
                    if not col_parts:
                        continue
                    first_token = col_parts[0].strip('"`\'[]').upper()
                    if first_token in ("CONSTRAINT", "PRIMARY", "FOREIGN", "INDEX", "KEY", "UNIQUE", "CHECK"):
                        continue

                    # Column definition: name type (handling parameters like DECIMAL(10, 2))
                    col_match = re.match(r"""^['"`]?(\w+)['"`]?\s+([A-Za-z0-9_]+(?:\s*\([^)]+\))?)""", line)
                    if col_match:
                        col_name = col_match.group(1)
                        col_type = re.sub(r"\s+", "", col_match.group(2)).upper()
                        is_pk = (
                            "PRIMARY KEY" in line.upper()
                            or col_name in table_pks
                            or "AUTOINCREMENT" in line.upper()
                            or "AUTO_INCREMENT" in line.upper()
                            or col_type in ("SERIAL", "BIGSERIAL", "SMALLSERIAL")
                        )

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

                    composite_pk_match = re.search(r"@@id\s*\(\s*\[(.*?)\]\s*\)", body)
                    composite_pks = set()
                    if composite_pk_match:
                        composite_pks = {f.strip() for f in composite_pk_match.group(1).split(",") if f.strip()}

                    for raw_line in body.splitlines():
                        line = raw_line.strip()
                        if not line or line.startswith("//") or line.startswith("@@"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            f_name = parts[0]
                            f_type = parts[1]
                            is_pk = "@id" in line or f_name in composite_pks

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
                        for col_m in re.finditer(r"@(Column|PrimaryColumn|PrimaryGeneratedColumn|ObjectIdColumn|CreateDateColumn|UpdateDateColumn|DeleteDateColumn)\s*\([^\)]*\)\s*([a-zA-Z0-9_]+)(?:\s*[:=]\s*([a-zA-Z0-9_]+))?", content):
                            col_type = col_m.group(3) or "any"
                            is_pk = col_m.group(1) in ("PrimaryGeneratedColumn", "PrimaryColumn", "ObjectIdColumn")
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
            # Match all Schema definitions: const XSchema = new Schema<Type>({ ... })
            schema_pattern = re.compile(
                r"""(?:(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*)?new\s+(?:mongoose\.)?Schema(?:<[^>]+>)?\s*\(""",
                re.MULTILINE,
            )

            for sm in schema_pattern.finditer(content):
                var_name = sm.group(1)
                # Find model name if declared: mongoose.model('User', ...) or model('User', ...)
                m_model = re.search(r"""(?:mongoose\.)?model\s*\(\s*['"]([a-zA-Z0-9_]+)['"]""", content)
                if m_model:
                    model_name = m_model.group(1)
                elif var_name:
                    model_name = re.sub(r"[sS]chema$", "", var_name) or var_name
                else:
                    model_name = file_path.stem

                start_pos = sm.end()
                brace_start = content.find("{", start_pos)
                if brace_start == -1 or (brace_start - start_pos > 20):
                    continue

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

                if brace_end == -1:
                    continue

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
                        if type_m:
                            col_type = type_m.group(1)
                        elif f_def.strip().startswith("["):
                            inner_tok = f_def.strip().lstrip("[").split()[0].rstrip("],{}")
                            col_type = f"Array<{inner_tok}>" if inner_tok else "Array"
                        else:
                            col_type = f_def.split()[0].rstrip(",{}")
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


import ast


def parse_python_models(root_path: Path):
    """Parse SQLAlchemy, Django, and Pydantic models with fields and foreign keys."""
    root_path = root_path.resolve()
    entities = {}
    relations = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        if file_path.suffix.lower() not in (".py", ".pyi"):
            continue

        rel = str(file_path.relative_to(root_path))
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check base classes
                    base_names = []
                    for b in node.bases:
                        if isinstance(b, ast.Name):
                            base_names.append(b.id)
                        elif isinstance(b, ast.Attribute):
                            base_names.append(b.attr)

                    is_model = any(
                        b in ("Base", "Model", "BaseModel", "DeclarativeBase", "SQLModel", "Document")
                        for b in base_names
                    )
                    if not is_model:
                        continue

                    model_name = node.name
                    columns = []

                    # Parse fields in class body
                    for item in node.body:
                        # 1. Type annotated models (Pydantic, SQLAlchemy 2.0 Mapped, Dataclasses)
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            f_name = item.target.id
                            f_type = "any"
                            if isinstance(item.annotation, ast.Name):
                                f_type = item.annotation.id
                            elif isinstance(item.annotation, ast.Attribute):
                                f_type = item.annotation.attr
                            elif isinstance(item.annotation, ast.Subscript) and hasattr(ast, "unparse"):
                                f_type = ast.unparse(item.annotation.slice)

                            val_str = ast.unparse(item.value) if (item.value and hasattr(ast, "unparse")) else ""
                            is_pk = "primary_key=True" in val_str or f_name == "id"

                            # SQLAlchemy 2.0 / SQLModel / Peewee ForeignKey check
                            if "ForeignKey" in val_str or "foreign_key" in val_str:
                                fk_m = re.search(r"""(?:ForeignKeyField|ForeignKey|foreign_key)\s*(?:\(\s*|=)\s*['"]?([a-zA-Z0-9_.]+)?['"]?""", val_str)
                                if fk_m and fk_m.group(1):
                                    fk_parts = fk_m.group(1).split(".")
                                    target_model = fk_parts[-1] if fk_parts[-1] and fk_parts[-1][0].isupper() else fk_parts[0]
                                    relations.append(
                                        {
                                            "from": model_name,
                                            "to": target_model,
                                            "from_column": f_name,
                                            "type": "foreign_key",
                                        }
                                    )

                            # Relationship / ManyToMany / OneToOne check
                            rel_check = re.search(r"""(?:relationship|ManyToManyField|OneToOneField)\s*\(\s*['"]?([a-zA-Z0-9_]+)['"]?""", val_str)
                            if rel_check:
                                target_model = rel_check.group(1)
                                relations.append(
                                    {
                                        "from": model_name,
                                        "to": target_model,
                                        "from_column": f_name,
                                        "type": "relationship",
                                    }
                                )
                            elif "relationship" in val_str:
                                m_inner = re.search(r"""(?:list|set|Sequence|Optional)?\[?([a-zA-Z0-9_]+)\]?""", f_type)
                                if m_inner and m_inner.group(1) not in ("any", "list", "set", "dict", "int", "str"):
                                    relations.append(
                                        {
                                            "from": model_name,
                                            "to": m_inner.group(1),
                                            "from_column": f_name,
                                            "type": "relationship",
                                        }
                                    )

                            columns.append({"name": f_name, "type": f_type, "primary_key": is_pk})

                        # 2. SQLAlchemy / Django style assignments: col = Column(...)
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    f_name = target.id
                                    val_str = ast.unparse(item.value) if hasattr(ast, "unparse") else ""
                                    is_pk = "primary_key=True" in val_str or f_name == "id"

                                    # Foreign key check
                                    if "ForeignKey" in val_str or "foreign_key" in val_str:
                                        fk_m = re.search(r"""(?:ForeignKeyField|ForeignKey|foreign_key)\s*(?:\(\s*|=)\s*['"]?([a-zA-Z0-9_.]+)?['"]?""", val_str)
                                        if fk_m and fk_m.group(1):
                                            fk_parts = fk_m.group(1).split(".")
                                            target_model = fk_parts[-1] if fk_parts[-1] and fk_parts[-1][0].isupper() else fk_parts[0]
                                            relations.append(
                                                {
                                                    "from": model_name,
                                                    "to": target_model,
                                                    "from_column": f_name,
                                                    "type": "foreign_key",
                                                }
                                            )

                                    # Relationship / ManyToMany / OneToOne check
                                    rel_check = re.search(r"""(?:relationship|ManyToManyField|OneToOneField)\s*\(\s*['"]?([a-zA-Z0-9_]+)['"]?""", val_str)
                                    if rel_check:
                                        target_model = rel_check.group(1)
                                        relations.append(
                                            {
                                                "from": model_name,
                                                "to": target_model,
                                                "from_column": f_name,
                                                "type": "relationship",
                                            }
                                        )

                                    col_type = "Column"
                                    if "models." in val_str:
                                        col_type = val_str.split("(")[0].replace("models.", "")
                                    elif "Column(" in val_str:
                                        col_type = "SQLAlchemy"

                                    columns.append({"name": f_name, "type": col_type, "primary_key": is_pk})

                    if "SQLModel" in base_names:
                        source_type = "SQLModel"
                    elif "Document" in base_names:
                        source_type = "Document/Beanie"
                    elif "BaseModel" in base_names:
                        source_type = "Pydantic"
                    else:
                        source_type = "SQLAlchemy/Django"
                    entities[model_name] = {
                        "name": model_name,
                        "file": rel,
                        "columns": columns,
                        "source": source_type,
                    }
        except Exception:
            pass

    return list(entities.values()), relations


def parse_other_data_models(root_path: Path):
    """Parse GORM structs (Go), JPA @Entity (Java), and Diesel/SeaORM (Rust) models and relations."""
    root_path = root_path.resolve()
    entities = {}
    relations = []

    for file_path in _common.walk_repo(root_path):
        if _common.is_binary(file_path):
            continue
        ext = file_path.suffix.lower()
        rel = str(file_path.relative_to(root_path))

        # 1. Go GORM structs
        if ext == ".go":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for m in re.finditer(r"type\s+([a-zA-Z0-9_]+)\s+struct\s*\{([^}]+)\}", content):
                    struct_name = m.group(1)
                    body = m.group(2)
                    if "gorm:" in body or "gorm.Model" in body:
                        columns = []
                        for line in body.splitlines():
                            parts = line.strip().split()
                            if len(parts) >= 2 and not parts[0].startswith("//"):
                                f_name = parts[0]
                                f_type = parts[1]
                                is_pk = "primaryKey" in line or f_name in ("ID", "Id")
                                columns.append({"name": f_name, "type": f_type, "primary_key": is_pk})
                                if (
                                    f_type not in ("string", "int", "int64", "uint", "uint64", "bool", "float64", "time.Time", "gorm.Model")
                                    and f_type[0].isupper()
                                ):
                                    target_struct = f_type.lstrip("[]*")
                                    relations.append(
                                        {
                                            "from": struct_name,
                                            "to": target_struct,
                                            "from_column": f_name,
                                            "type": "gorm_relation",
                                        }
                                    )
                        entities[struct_name] = {
                            "name": struct_name,
                            "file": rel,
                            "columns": columns,
                            "source": "GORM",
                        }
            except Exception:
                pass

        # 2. Java / JPA @Entity
        elif ext in (".java", ".kt"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "@Entity" in content:
                    m_cls = re.search(r"@Entity[^{]*?class\s+([a-zA-Z0-9_]+)", content, re.DOTALL)
                    if m_cls:
                        class_name = m_cls.group(1)
                        columns = []
                        for line in content.splitlines():
                            m_field = re.search(r"""(?:private|protected|public)\s+([a-zA-Z0-9_<>]+)\s+([a-zA-Z0-9_]+)\s*;""", line)
                            if m_field:
                                f_type = m_field.group(1)
                                f_name = m_field.group(2)
                                is_pk = f_name.lower() == "id" or "@Id" in line
                                columns.append({"name": f_name, "type": f_type, "primary_key": is_pk})

                        # Extract JPA relationships
                        for rel_m in re.finditer(
                            r"""@(ManyToOne|OneToMany|OneToOne|ManyToMany)[^;]*?(?:private|protected|public)\s+([a-zA-Z0-9_<>]+)\s+([a-zA-Z0-9_]+)\s*;""",
                            content,
                            re.DOTALL,
                        ):
                            rel_type = rel_m.group(1)
                            raw_target = rel_m.group(2)
                            target_entity = re.sub(r"""^(?:List|Set|Collection)<([a-zA-Z0-9_]+)>$""", r"\1", raw_target)
                            relations.append(
                                {
                                    "from": class_name,
                                    "to": target_entity,
                                    "from_column": rel_m.group(3),
                                    "type": f"jpa_{rel_type}",
                                }
                            )

                        entities[class_name] = {
                            "name": class_name,
                            "file": rel,
                            "columns": columns,
                            "source": "JPA/Hibernate",
                        }
            except Exception:
                pass

        # 3. Rust Diesel / SeaORM
        elif ext == ".rs":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "derive(Queryable" in content or "derive(DeriveEntityModel" in content or "#[table_name" in content:
                    m_struct = re.search(r"(?:#\[[^\]]+\]\s*)*pub\s+struct\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}", content)
                    if m_struct:
                        struct_name = m_struct.group(1)
                        body = m_struct.group(2)
                        columns = []
                        for line in body.splitlines():
                            m_f = re.search(r"""(?:pub\s+)?([a-zA-Z0-9_]+)\s*:\s*([^,]+)""", line)
                            if m_f:
                                f_name = m_f.group(1)
                                f_type = m_f.group(2).strip()
                                is_pk = f_name == "id"
                                columns.append({"name": f_name, "type": f_type, "primary_key": is_pk})
                        entities[struct_name] = {
                            "name": struct_name,
                            "file": rel,
                            "columns": columns,
                            "source": "Diesel/SeaORM",
                        }
            except Exception:
                pass

    return list(entities.values()), relations


def render_mermaid_erd(entities: list, relations: list, max_entities: int = 25) -> str:
    """Render Mermaid erDiagram markup capped at max_entities."""
    lines = ["erDiagram"]

    if not entities:
        lines.append("  EMPTY_SCHEMA {\n    string note\n  }")
        return "\n".join(lines)

    # Cap entities at max_entities
    selected_entities = entities[:max_entities]
    selected_names = {e["name"] for e in selected_entities}
    name_map = {e["name"]: re.sub(r"[^a-zA-Z0-9_]", "_", e["name"]).strip("_") or "Entity" for e in selected_entities}

    # Render relationships for selected entities
    rendered_relations = set()
    for rel in relations:
        src = rel.get("from")
        tgt = rel.get("to")
        if src in selected_names and tgt in selected_names:
            safe_src = name_map[src]
            safe_tgt = name_map[tgt]
            rel_key = (safe_src, safe_tgt)
            if rel_key not in rendered_relations:
                rendered_relations.add(rel_key)
                # Mermaid ERD syntax: A ||--o{ B : "references"
                lines.append(f'  {safe_src} ||--o{{ {safe_tgt} : "references"')

    # Render entity field blocks
    for ent in selected_entities:
        name = name_map[ent["name"]]
        cols = ent.get("columns", [])
        if cols:
            lines.append(f"  {name} {{")
            for c in cols[:12]:  # cap columns per entity to keep readable
                c_name = re.sub(r"[^a-zA-Z0-9_]", "_", c["name"]).strip("_") or "field"
                c_type = re.sub(r"[^a-zA-Z0-9_]", "_", c.get("type", "string")).strip("_") or "string"
                pk_marker = " PK" if c.get("primary_key") else ""
                lines.append(f"    {c_type} {c_name}{pk_marker}")
            lines.append("  }")
        else:
            lines.append(f"  {name} {{\n    string id PK\n  }}")

    return "\n".join(lines)


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
    python_entities, python_relations = parse_python_models(root_path)
    other_entities, other_relations = parse_other_data_models(root_path)

    all_entities = (
        sql_entities
        + prisma_entities
        + mongoose_entities
        + python_entities
        + other_entities
    )
    all_relations = (
        sql_relations
        + prisma_relations
        + mongoose_relations
        + python_relations
        + other_relations
    )

    data = {
        "root": str(root_path),
        "entities": all_entities,
        "relations": all_relations,
    }

    if args.json:
        _common.output_json(data)
    elif args.mermaid:
        print(render_mermaid_erd(all_entities, all_relations, max_entities=25))
    else:
        print(f"Data Model Extraction for: {root_path}")
        print(f"Entities discovered: {len(all_entities)}")
        print(f"Relationships discovered: {len(all_relations)}")
        for ent in all_entities:
            print(f"\n[{ent['source']}] {ent['name']} ({len(ent.get('columns', []))} columns) - {ent['file']}")
            for c in ent.get("columns", [])[:5]:
                pk = " [PK]" if c.get("primary_key") else ""
                print(f"  - {c['name']}: {c['type']}{pk}")


if __name__ == "__main__":
    main()
