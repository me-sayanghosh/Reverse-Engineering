# Ecosystem Analysis Playbook

Guidance on where to look first, common patterns, and architecture pitfalls across 10 major software ecosystems.

## 1. Node/TypeScript Ecosystem

- **Where to look first (Entrypoints)**: Inspect `package.json` for `"main"`, `"bin"`, and `"scripts.start"`. Common entry files include `src/index.ts`, `src/server.ts`, `src/main.ts`, or `src/app.ts`.
- **Routing & Controllers**: Locate router instances (`express.Router()`, Fastify plugins, NestJS `@Controller()` decorators). Check `src/routes/`, `src/controllers/`, or `src/api/`.
- **State Management & DI**: For backends, look for dependency injection containers (NestJS modules, InversifyJS, TSyringe). For frontends, inspect Redux Toolkit slices, Zustand stores, or React Context providers.
- **Database Layer**: Check for Prisma (`prisma/schema.prisma`), TypeORM (`src/entities/`), Mongoose (`src/models/`), Drizzle (`drizzle/schema.ts`), or raw Knex/Kysely migrations.
- **Configuration & Secrets**: Inspect `dotenv` usage (`.env.example`), `config/` packages, or `process.env` references wrapped in schema validation like Zod or Joi.
- **Common Architectural Patterns**: Layered controller-service-repository pattern, modular plugins (Fastify), middleware request pipelines, event emitters for domain events.
- **Common Pitfalls**: Missing async error handling in Express (unhandled promise rejections), circular module dependencies via `index.ts` barrel files, loose `any` types masking schema mismatches.
- **Testing & Tooling**: Look for Jest (`jest.config.js`), Vitest (`vitest.config.ts`), ESLint, and TypeScript compiler configuration (`tsconfig.json`).

## 2. Python Ecosystem

- **Where to look first (Entrypoints)**: Check `pyproject.toml` (`[project.scripts]`), `setup.py`, `wsgi.py`, `asgi.py`, or `__main__.py`. For Django, start at `manage.py` and `wsgi.py`.
- **Routing & Views**: For FastAPI, inspect `APIRouter` instances in `app/routers/`. For Flask, check `Blueprint` files in `app/views/`. For Django, inspect `urls.py` in the root configuration directory.
- **Data Models & ORM**: Inspect SQLAlchemy models in `models.py` or `db/base.py`, Django models in `app/models.py`, or Tortoise/SQLModel classes.
- **Application Configuration**: Check `settings.py` (Django), `pydantic-settings` (`BaseSettings`), `config.py`, or environment variable reads via `os.environ` / `os.getenv`.
- **Background Jobs & Tasks**: Inspect Celery task definitions (`@celery.task`), Dramatiq actors, or RQ worker queues in `tasks.py` or `workers/`.
- **Common Architectural Patterns**: FastAPI dependency injection (`Depends()`), Django MVT (Model-View-Template) with class-based views, application factories (`create_app()`).
- **Common Pitfalls**: Blocking synchronous I/O calls inside async coroutines in FastAPI/AsyncIO, mutable default arguments in function signatures, circular imports across model modules.
- **Testing & Packaging**: Locate `pytest.ini`, `conftest.py`, `tests/` directory, and dependency definitions in `pyproject.toml` (Poetry/Hatch/Flit/PDM) or `requirements.txt`.

## 3. Go Ecosystem
TODO

## 4. Rust Ecosystem
TODO

## 5. Java and Kotlin Ecosystem
TODO

## 6. .NET and C# Ecosystem
TODO

## 7. Ruby Ecosystem
TODO

## 8. PHP Ecosystem
TODO

## 9. Mobile (Android, iOS, Flutter, React Native)
TODO

## 10. Machine Learning and Data Engineering Repositories
TODO
