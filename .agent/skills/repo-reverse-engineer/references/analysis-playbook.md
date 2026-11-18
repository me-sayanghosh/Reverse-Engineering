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

- **Where to look first (Entrypoints)**: Check `cmd/<app>/main.go` or root `main.go`. Read `go.mod` to identify module path and dependencies.
- **Routing & HTTP**: Look for Gin (`gin.Default()`), Echo (`echo.New()`), Chi, or standard library `net/http` handlers in `internal/api/` or `pkg/`.
- **Package Layout & Domain**: Standard Go layout splits code into `cmd/` (executables), `internal/` (private app logic), and `pkg/` (exported libraries).
- **Concurrency & Goroutines**: Look for channel communication (`chan`), `sync.WaitGroup`, worker pools, and context cancellation propagation (`ctx context.Context`).
- **Data Access Layer**: Check for GORM models, sqlx query definitions, ent schemas, or raw database migration files in `migrations/`.
- **Common Pitfalls**: Unhandled goroutine leaks without context cancellation, ignoring errors (`_ = fn()`), race conditions without mutex protection.

## 4. Rust Ecosystem

- **Where to look first (Entrypoints)**: Inspect `Cargo.toml`. Entrypoints reside in `src/main.rs` (binary) or `src/lib.rs` (library), plus multiple binaries in `src/bin/`.
- **Web Frameworks & Async Runtime**: Tokio runtime macros (`#[tokio::main]`), Actix-web (`HttpServer::new`), Axum routers, or Tower middleware services.
- **Data Models & Types**: Inspect `struct` and `enum` declarations, `serde::Serialize` / `Deserialize` derives, and database mappings (Diesel schemas, SQLx query macros, SeaORM).
- **Error Handling**: Look for `Result<T, E>`, `thiserror` enum error types, and `anyhow::Result` propagation across module boundaries.
- **Concurrency & Safety**: Inspect `Arc<Mutex<T>>` or `RwLock<T>` shared state, crossbeam channels, and Rayon parallel iterators.
- **Common Pitfalls**: Overly restrictive lifetime bounds leading to clone overhead, complex macro expansions masking control flow.

## 5. Java and Kotlin Ecosystem

- **Where to look first (Entrypoints)**: Check `pom.xml` (Maven) or `build.gradle` / `build.gradle.kts` (Gradle). Locate `@SpringBootApplication` or classes containing `public static void main`.
- **Dependency Injection & Routing**: Inspect Spring `@RestController`, `@Service`, `@Repository`, and `@Component` annotations. For Kotlin, check Ktor routing blocks.
- **Persistence & ORM**: Inspect JPA entities (`@Entity`), Spring Data repositories (`JpaRepository`), Hibernate mapping configurations, or Exposed/jOOQ queries.
- **Build & Multi-module**: Check parent POM / multi-project Gradle settings (`settings.gradle`) defining subprojects and shared library modules.
- **Common Pitfalls**: JPA N+1 query execution bottlenecks, excessive reflection slowing startup times, memory leaks from improper thread-local handling.

## 6. .NET and C# Ecosystem

- **Where to look first (Entrypoints)**: Inspect `*.csproj` and `*.sln` files. Modern .NET starts at `Program.cs` with top-level statements and `WebApplication.CreateBuilder`.
- **Routing & Controllers**: Look for ASP.NET Core minimal APIs (`app.MapGet()`, `app.MapPost()`) or controller classes inheriting from `ControllerBase`.
- **Dependency Injection & Middleware**: Inspect service registration (`builder.Services.AddScoped()`, `AddSingleton()`) and middleware pipeline configuration (`app.UseAuthentication()`).
- **Data Access & ORM**: Inspect Entity Framework Core (`DbContext`, `DbSet<T>`), Dapper queries, or migration scripts in `Migrations/`.
- **Common Pitfalls**: Async void event handlers masking exceptions, improper `HttpClient` lifecycle instantiations causing socket exhaustion.

## 7. Ruby Ecosystem

- **Where to look first (Entrypoints)**: Inspect `Gemfile`. For Rails, look at `config.ru`, `bin/rails`, and `config/routes.rb`. For Sinatra, inspect the main `app.rb` file.
- **MVC Architecture**: Rails strictly organizes code into `app/controllers/`, `app/models/` (ActiveRecord), and `app/views/` (or API-only serializers).
- **ActiveRecord Models & Migrations**: Inspect database schema in `db/schema.rb` and database migrations in `db/migrate/`. Check model associations (`has_many`, `belongs_to`).
- **Background Jobs**: Inspect ActiveJob configurations, Sidekiq worker classes in `app/workers/`, or Resque definitions.
- **Common Pitfalls**: Unscoped ActiveRecord queries leaking tenant data, N+1 query loading without `includes`, monkey patching core classes.

## 8. PHP Ecosystem

- **Where to look first (Entrypoints)**: Inspect `composer.json` for dependencies and autoload rules. Web requests enter at `public/index.php`.
- **Framework Structure**: For Laravel, inspect `routes/web.php` and `routes/api.php`, controllers in `app/Http/Controllers/`, and Eloquent models in `app/Models/`.
- **Database & Eloquent**: Check migrations in `database/migrations/` and relationships declared on models (`hasMany`, `belongsTo`).
- **Service Container & Providers**: Inspect service providers in `app/Providers/` configuring bindings and application bootstrapping.
- **Common Pitfalls**: Reliance on global helpers bypassing dependency injection, unindexed Eloquent queries, improper output sanitization.

## 9. Mobile (Android, iOS, Flutter, React Native)

- **Where to look first (Entrypoints)**: Android: `MainActivity.kt` / `AndroidManifest.xml`. iOS: `AppDelegate.swift` or `@main struct App`. Flutter: `lib/main.dart`. React Native: `App.tsx` or `index.js`.
- **Navigation & Routing**: Android Jetpack Navigation / Compose Navigation; iOS SwiftUI `NavigationStack`; Flutter `GoRouter` or Navigator 2.0; React Navigation.
- **State Management**: Android ViewModel + StateFlow; iOS `@Observable` / `@StateObject`; Flutter BLoC, Riverpod, or Provider; React Native Redux or Zustand.
- **Local Storage & Database**: Android Room database; iOS SwiftData / CoreData; Flutter Hive / Isar / SQLite; React Native MMKV / AsyncStorage.
- **Common Pitfalls**: Blocking the main UI thread with heavy computational or disk tasks, improper lifecycle teardown causing background memory leaks.

## 10. Machine Learning and Data Engineering Repositories

- **Where to look first (Entrypoints)**: Look for pipeline runner scripts (`train.py`, `evaluate.py`, `pipeline.py`), Jupyter notebooks (`notebooks/`), or orchestrator DAGs.
- **Data Ingestion & Preprocessing**: Locate dataset loaders (`torch.utils.data.Dataset`, Pandas/Polars pipelines, PySpark transformation scripts).
- **Model Architecture & Graphs**: Inspect neural network class definitions (`torch.nn.Module`, Keras `Model`, scikit-learn estimators).
- **Pipelines & Orchestration**: Check for Airflow DAGs (`dags/`), Prefect flows, Kubeflow pipeline configs, or DVC pipeline files (`dvc.yaml`).
- **Common Pitfalls**: Silent data leakage between train and test splits, unversioned random seeds breaking reproducibility, missing GPU memory cleanup.
