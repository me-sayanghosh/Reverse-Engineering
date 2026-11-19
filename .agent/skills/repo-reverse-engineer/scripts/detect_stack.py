#!/usr/bin/env python3
"""Detect ecosystems, frameworks, databases, infrastructure, and commands in a repository."""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _common

MANIFEST_TO_ECOSYSTEM: dict[str, str] = {
    "package.json": "Node/TypeScript",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "Pipfile": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "build.gradle.kts": "Kotlin/Gradle",
    "build.sbt": "Scala",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "pubspec.yaml": "Dart/Flutter",
    "Package.swift": "Swift",
    "mix.exs": "Elixir",
    "rebar.config": "Erlang",
    "deno.json": "Deno/TypeScript",
    "deno.jsonc": "Deno/TypeScript",
    "bunfig.toml": "Bun",
    "stack.yaml": "Haskell",
    "cabal.project": "Haskell",
    "shard.yml": "Crystal",
    "dune-project": "OCaml",
    ".csproj": ".NET/C#",
    ".fsproj": ".NET/F#",
    ".sln": ".NET",
}


def detect_manifests(root_path: Path):
    """Detect package manifests and identify associated ecosystems."""
    root_path = Path(root_path).resolve()
    found_manifests = []
    ecosystems = set()

    for file_path in _common.walk_repo(root_path):
        name = file_path.name
        rel_path = str(file_path.relative_to(root_path))
        matched = False

        if name in MANIFEST_TO_ECOSYSTEM:
            eco = MANIFEST_TO_ECOSYSTEM[name]
            found_manifests.append({"path": rel_path, "manifest": name, "ecosystem": eco})
            ecosystems.add(eco)
            matched = True
        elif name.startswith("requirements") and name.endswith(".txt"):
            eco = MANIFEST_TO_ECOSYSTEM["requirements.txt"]
            found_manifests.append({"path": rel_path, "manifest": name, "ecosystem": eco})
            ecosystems.add(eco)
            matched = True
        elif file_path.suffix in (".csproj", ".fsproj", ".sln"):
            eco = MANIFEST_TO_ECOSYSTEM.get(file_path.suffix, ".NET")
            found_manifests.append({"path": rel_path, "manifest": name, "ecosystem": eco})
            ecosystems.add(eco)
            matched = True

    return sorted(list(ecosystems)), found_manifests


NODE_PKG_TO_FRAMEWORK: dict[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt",
    "svelte": "Svelte",
    "@angular/core": "Angular",
    "express": "Express",
    "fastify": "Fastify",
    "@nestjs/core": "NestJS",
    "@nestjs/common": "NestJS",
    "koa": "Koa",
    "hono": "Hono",
    "prisma": "Prisma",
    "@prisma/client": "Prisma",
    "mongoose": "Mongoose",
    "socket.io": "Socket.IO",
    "vite": "Vite",
    "webpack": "Webpack",
    "jest": "Jest",
    "vitest": "Vitest",
    "tailwindcss": "Tailwind CSS",
    "@trpc/server": "tRPC",
    "astro": "Astro",
    "@remix-run/react": "Remix",
    "@remix-run/node": "Remix",
    "gatsby": "Gatsby",
    "solid-js": "Solid",
    "@builder.io/qwik": "Qwik",
    "electron": "Electron",
    "playwright": "Playwright",
    "@playwright/test": "Playwright",
    "cypress": "Cypress",
    "graphql": "GraphQL",
    "@apollo/server": "Apollo GraphQL",
    "bull": "Bull",
    "bullmq": "BullMQ",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "knex": "Knex",
    "drizzle-orm": "Drizzle ORM",
    "commander": "Commander",
    "yargs": "Yargs",
}


def detect_node_frameworks(root_path: Path):
    """Parse all package.json files for known Node/TS frameworks and libraries."""
    root_path = Path(root_path).resolve()
    frameworks = set()
    import json

    for file_path in _common.walk_repo(root_path):
        if file_path.name == "package.json":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {}
                    deps.update(data.get("dependencies", {}))
                    deps.update(data.get("devDependencies", {}))
                    deps.update(data.get("peerDependencies", {}))
                    for dep in deps:
                        if dep in NODE_PKG_TO_FRAMEWORK:
                            frameworks.add(NODE_PKG_TO_FRAMEWORK[dep])
            except Exception:
                pass
    return sorted(list(frameworks))


PYTHON_PKG_TO_FRAMEWORK: dict[str, str] = {
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "starlette": "Starlette",
    "litestar": "Litestar",
    "sqlalchemy": "SQLAlchemy",
    "celery": "Celery",
    "pydantic": "Pydantic",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "pytest": "pytest",
    "tornado": "Tornado",
    "sanic": "Sanic",
    "aiohttp": "aiohttp",
    "gunicorn": "Gunicorn",
    "uvicorn": "Uvicorn",
    "alembic": "Alembic",
    "peewee": "Peewee",
    "tortoise": "Tortoise-ORM",
    "beanie": "Beanie",
    "click": "Click",
    "typer": "Typer",
    "polars": "Polars",
    "pandas": "Pandas",
    "scipy": "SciPy",
    "numpy": "NumPy",
    "scrapy": "Scrapy",
}


def detect_python_frameworks(root_path: Path):
    """Parse requirements.txt, pyproject.toml, Pipfile, setup.py, setup.cfg for known Python frameworks."""
    root_path = Path(root_path).resolve()
    frameworks = set()
    import re

    for file_path in _common.walk_repo(root_path):
        name = file_path.name.lower()
        if (
            (name.startswith("requirements") and name.endswith(".txt"))
            or name in ("pyproject.toml", "pipfile", "setup.cfg", "setup.py")
        ):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                    for pkg, fw in PYTHON_PKG_TO_FRAMEWORK.items():
                        # Match word boundaries or dependency specifiers (allowing extras like [all])
                        pattern = rf"(?:^|[\"'\s,\[])({re.escape(pkg)})(?:[=><~!\s\"',\]\[]|$)"
                        if re.search(pattern, content, re.MULTILINE):
                            frameworks.add(fw)
            except Exception:
                pass

    return sorted(list(frameworks))


OTHER_FRAMEWORKS_MAP = {
    # Go (go.mod)
    "go.mod": {
        "github.com/gin-gonic/gin": "Gin",
        "github.com/labstack/echo": "Echo",
        "github.com/gofiber/fiber": "Fiber",
        "github.com/go-chi/chi": "Chi",
        "github.com/gorilla/mux": "Gorilla Mux",
        "github.com/spf13/cobra": "Cobra",
        "gorm.io/gorm": "GORM",
        "github.com/jmoiron/sqlx": "Sqlx",
        "entgo.io/ent": "Ent",
        "google.golang.org/grpc": "gRPC",
    },
    # Rust (Cargo.toml)
    "Cargo.toml": {
        "actix-web": "Actix",
        "axum": "Axum",
        "tokio": "Tokio",
        "rocket": "Rocket",
        "warp": "Warp",
        "poem": "Poem",
        "diesel": "Diesel",
        "sea-orm": "SeaORM",
        "sqlx": "SQLx",
        "clap": "Clap",
        "serde": "Serde",
        "tonic": "Tonic (gRPC)",
    },
    # Ruby (Gemfile)
    "Gemfile": {
        "rails": "Rails",
        "sinatra": "Sinatra",
    },
    # PHP (composer.json)
    "composer.json": {
        "laravel/framework": "Laravel",
        "symfony/framework-bundle": "Symfony",
    },
}


def detect_other_frameworks(root_path: Path):
    """Detect Go, Rust, Java, Ruby, PHP, .NET frameworks from manifest contents."""
    root_path = Path(root_path).resolve()
    frameworks = set()

    for file_path in _common.walk_repo(root_path):
        name = file_path.name
        # Go, Rust, Ruby, PHP
        if name in OTHER_FRAMEWORKS_MAP:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for key, fw in OTHER_FRAMEWORKS_MAP[name].items():
                    if key in content:
                        frameworks.add(fw)
            except Exception:
                pass

        # Java / Kotlin (pom.xml, build.gradle, build.gradle.kts)
        if name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "spring-boot" in content or "org.springframework.boot" in content:
                    frameworks.add("Spring Boot")
                if "io.quarkus" in content:
                    frameworks.add("Quarkus")
                if "io.micronaut" in content:
                    frameworks.add("Micronaut")
            except Exception:
                pass

        # C# (.csproj)
        if file_path.suffix == ".csproj":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if "Microsoft.AspNetCore" in content or "Microsoft.NET.Sdk.Web" in content:
                    frameworks.add("ASP.NET")
            except Exception:
                pass

    return sorted(list(frameworks))


def detect_infra(root_path: Path):
    """Detect infrastructure configurations: Docker, Compose, K8s, Terraform, Helm, Serverless, CI, Vercel, Netlify."""
    root_path = Path(root_path).resolve()
    infra = []
    seen_types = set()

    for file_path in _common.walk_repo(root_path):
        name = file_path.name.lower()
        rel_path = str(file_path.relative_to(root_path))

        if name == "dockerfile" or name.startswith("dockerfile.") or name == "containerfile":
            if "Docker" not in seen_types:
                infra.append({"type": "Docker", "file": rel_path})
                seen_types.add("Docker")
        elif name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
            if "Docker Compose" not in seen_types:
                infra.append({"type": "Docker Compose", "file": rel_path})
                seen_types.add("Docker Compose")
        elif file_path.suffix in (".tf", ".tfvars"):
            if "Terraform" not in seen_types:
                infra.append({"type": "Terraform", "file": rel_path})
                seen_types.add("Terraform")
        elif name == "chart.yaml" or "helm" in file_path.parts:
            if "Helm" not in seen_types:
                infra.append({"type": "Helm", "file": rel_path})
                seen_types.add("Helm")
        elif name in ("serverless.yml", "serverless.yaml", "serverless.ts"):
            if "Serverless Framework" not in seen_types:
                infra.append({"type": "Serverless Framework", "file": rel_path})
                seen_types.add("Serverless Framework")
        elif name == "vercel.json":
            if "Vercel" not in seen_types:
                infra.append({"type": "Vercel", "file": rel_path})
                seen_types.add("Vercel")
        elif name == "netlify.toml":
            if "Netlify" not in seen_types:
                infra.append({"type": "Netlify", "file": rel_path})
                seen_types.add("Netlify")
        elif ".github" in file_path.parts and "workflows" in file_path.parts and (name.endswith(".yml") or name.endswith(".yaml")):
            if "GitHub Actions" not in seen_types:
                infra.append({"type": "GitHub Actions", "file": rel_path})
                seen_types.add("GitHub Actions")
        elif name in (".gitlab-ci.yml", ".gitlab-ci.yaml"):
            if "GitLab CI" not in seen_types:
                infra.append({"type": "GitLab CI", "file": rel_path})
                seen_types.add("GitLab CI")
        elif ".circleci" in file_path.parts:
            if "CircleCI" not in seen_types:
                infra.append({"type": "CircleCI", "file": rel_path})
                seen_types.add("CircleCI")
        elif name in ("azure-pipelines.yml", "azure-pipelines.yaml"):
            if "Azure Pipelines" not in seen_types:
                infra.append({"type": "Azure Pipelines", "file": rel_path})
                seen_types.add("Azure Pipelines")
        elif name in ("cloudbuild.yaml", "cloudbuild.yml"):
            if "Cloud Build" not in seen_types:
                infra.append({"type": "Cloud Build", "file": rel_path})
                seen_types.add("Cloud Build")
        elif "k8s" in file_path.parts or "kubernetes" in file_path.parts or name.endswith(".k8s.yaml"):
            if "Kubernetes" not in seen_types:
                infra.append({"type": "Kubernetes", "file": rel_path})
                seen_types.add("Kubernetes")

    return infra


DATASTORE_PATTERNS = {
    "PostgreSQL": ["postgres", "postgresql", "psycopg2", "asyncpg", '"pg"', "'pg'", "libpq"],
    "MySQL": ["mysql", "mysql2", "pymysql", "mysqlclient"],
    "MongoDB": ["mongodb", "mongoose", "pymongo", "motor"],
    "Redis": ["redis", "ioredis", "aioredis"],
    "SQLite": ["sqlite", "sqlite3", "better-sqlite3", "rusqlite"],
    "Kafka": ["kafka", "kafkajs", "confluent-kafka", "aiokafka", "sarama"],
    "RabbitMQ": ["amqp", "amqplib", "pika", "rabbitmq"],
    "SQS": ["client-sqs", "sqs"],
    "Elasticsearch": ["elasticsearch", "@elastic/elasticsearch", "opensearch"],
    "ClickHouse": ["clickhouse", "clickhouse-driver", "@clickhouse/client"],
    "Cassandra": ["cassandra", "cassandra-driver", "scylladb", "gocql"],
    "Neo4j": ["neo4j", "neomodel", "py2neo"],
    "DynamoDB": ["dynamodb", "client-dynamodb"],
    "CouchDB": ["couchdb", "couchbase"],
    "CockroachDB": ["cockroach", "cockroachdb"],
}


def detect_datastores_and_queues(root_path: Path):
    """Detect databases and message queues from dependencies and config files."""
    root_path = Path(root_path).resolve()
    detected = set()

    # Scan manifest files and compose files
    candidate_names = {
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pipfile",
        "go.mod",
        "cargo.toml",
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "schema.prisma",
        "settings.py",
        "application.properties",
        "application.yml",
        "application.yaml",
    }

    for file_path in _common.walk_repo(root_path):
        if file_path.name.lower() in candidate_names or file_path.suffix.lower() == ".prisma":
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                for store, patterns in DATASTORE_PATTERNS.items():
                    for pat in patterns:
                        if pat.lower() in content:
                            detected.add(store)
                            break
            except Exception:
                pass

    return sorted(list(detected))


def infer_commands(root_path: Path, ecosystems: list):
    """Infer install, build, test, and start commands from package scripts, Makefiles, and manifests."""
    root_path = Path(root_path).resolve()
    commands = {}

    # Check Node / package.json
    pkg_json = root_path / "package.json"
    if pkg_json.exists():
        try:
            import json

            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                scripts = data.get("scripts", {})
                pm = "npm"
                if (root_path / "pnpm-lock.yaml").exists():
                    pm = "pnpm"
                elif (root_path / "yarn.lock").exists():
                    pm = "yarn"
                elif (root_path / "bun.lockb").exists() or (root_path / "bun.lock").exists():
                    pm = "bun"

                commands["install"] = f"{pm} install"
                if "build" in scripts:
                    commands["build"] = f"{pm} run build"
                if "test" in scripts:
                    commands["test"] = f"{pm} test"
                if "start" in scripts:
                    commands["start"] = f"{pm} start"
                elif "dev" in scripts:
                    commands["start"] = f"{pm} run dev"
        except Exception:
            pass

    # Check Makefile
    makefile = root_path / "Makefile"
    if makefile.exists():
        try:
            content = makefile.read_text(encoding="utf-8", errors="ignore")
            import re

            targets = set(re.findall(r"^([a-zA-Z0-9_-]+):", content, re.MULTILINE))
            if "build" in targets and "build" not in commands:
                commands["build"] = "make build"
            if "test" in targets and "test" not in commands:
                commands["test"] = "make test"
            if "run" in targets and "start" not in commands:
                commands["start"] = "make run"
        except Exception:
            pass

    # Check README code blocks per Step 44
    readme_candidates = [root_path / "README.md", root_path / "readme.md", root_path / "README.rst"]
    for rmp in readme_candidates:
        if rmp.exists():
            try:
                import re
                rm_text = rmp.read_text(encoding="utf-8", errors="ignore")
                code_blocks = re.findall(r"```(?:bash|sh|shell|console)?\s*\n(.*?)\n```", rm_text, re.DOTALL)
                for block in code_blocks:
                    for raw_l in block.splitlines():
                        line = raw_l.strip().lstrip("$ ").strip()
                        if not line or line.startswith("#"):
                            continue
                        if "install" not in commands and any(line.startswith(c) for c in ["npm install", "yarn install", "pnpm install", "pip install", "poetry install"]):
                            commands["install"] = line
                        if "start" not in commands and any(line.startswith(c) for c in ["npm start", "npm run dev", "yarn start", "python ", "python3 ", "node ", "cargo run", "go run"]):
                            commands["start"] = line
                        if "test" not in commands and any(line.startswith(c) for c in ["npm test", "pytest", "cargo test", "go test"]):
                            commands["test"] = line
                        if "build" not in commands and any(line.startswith(c) for c in ["npm run build", "yarn build", "cargo build", "go build"]):
                            commands["build"] = line
            except Exception:
                pass
            break

    # Fallback by ecosystem if not already discovered
    if "Python" in ecosystems or any("Python" in e for e in ecosystems):
        commands.setdefault("install", "pip install -r requirements.txt")
        commands.setdefault("test", "pytest")
        commands.setdefault("start", "python main.py")
    elif "Go" in ecosystems:
        commands.setdefault("build", "go build ./...")
        commands.setdefault("test", "go test ./...")
        commands.setdefault("start", "go run main.go")
    elif "Rust" in ecosystems:
        commands.setdefault("build", "cargo build")
        commands.setdefault("test", "cargo test")
        commands.setdefault("start", "cargo run")
    elif any("Deno" in e for e in ecosystems):
        commands.setdefault("test", "deno test")
        commands.setdefault("start", "deno run main.ts")

    return commands


def detect_suspicious_scripts(root_path: Path):
    """Detect high-risk lifecycle hooks (postinstall, preinstall) or suspicious payload commands."""
    root_path = Path(root_path).resolve()
    risks = []
    for pkg_json in _common.walk_repo(root_path):
        if pkg_json.name == "package.json":
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
                scripts = data.get("scripts", {})
                for hook in ["postinstall", "preinstall", "install"]:
                    if hook in scripts:
                        val = str(scripts[hook])
                        rel = str(pkg_json.relative_to(root_path))
                        risks.append({
                            "file": rel,
                            "hook": hook,
                            "command": val,
                            "warning": f"Suspicious lifecycle hook '{hook}' in {rel}: {val}"
                        })
            except Exception:
                pass
    return risks


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect repository technology stack, frameworks, databases, and build/run commands."
    )
    parser.add_argument("root", help="Path to repository root directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        _common.die(f"Repository root does not exist: {root_path}")

    ecosystems, manifests = detect_manifests(root_path)
    all_fws = (
        detect_node_frameworks(root_path)
        + detect_python_frameworks(root_path)
        + detect_other_frameworks(root_path)
    )
    frameworks = sorted(list(set(all_fws)))
    infra = detect_infra(root_path)
    datastores = detect_datastores_and_queues(root_path)
    commands = infer_commands(root_path, ecosystems)
    suspicious_scripts = detect_suspicious_scripts(root_path)

    data = {
        "root": str(root_path),
        "ecosystems": ecosystems,
        "manifests": manifests,
        "frameworks": frameworks,
        "datastores": datastores,
        "infra": infra,
        "commands": commands,
        "suspicious_scripts": suspicious_scripts,
        "confidence": "high" if (ecosystems or frameworks) else "medium",
    }

    if args.json:
        _common.output_json(data)
    else:
        print(f"Stack Detection for: {root_path}")
        print(f"Confidence: {data['confidence']}")
        print(f"Ecosystems: {', '.join(ecosystems) if ecosystems else 'None detected'}")
        print(f"Frameworks: {', '.join(frameworks) if frameworks else 'None detected'}")
        print(f"Datastores: {', '.join(datastores) if datastores else 'None detected'}")
        print(f"Infrastructure: {', '.join(i['type'] for i in infra) if infra else 'None detected'}")
        print("Inferred Commands:")
        for k, v in commands.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
