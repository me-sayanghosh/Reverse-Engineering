# 01 - Architecture & Component Decomposition: node-express-realworld-example-app

## System Architecture
The application adheres to a clean layered Controller-Service architectural pattern:

```
HTTP Clients
    │
    ▼
src/main.ts:7 (Express App)
    ├─► src/app/routes/routes.ts:13 (/api router)
    │       ├─► src/app/routes/auth/auth.controller.ts:15 (/api/users)
    │       │        └─► src/app/routes/auth/auth.service.ts:10
    │       ├─► src/app/routes/article/article.controller.ts:25 (/api/articles)
    │       │        └─► src/app/routes/article/article.service.ts:15
    │       ├─► src/app/routes/profile/profile.controller.ts:10 (/api/profiles)
    │       │        └─► src/app/routes/profile/profile.service.ts:5
    │       └─► src/app/routes/tag/tag.controller.ts:5 (/api/tags)
    │                └─► src/app/routes/tag/tag.service.ts:4
    │
    └─► src/prisma/prisma-client.ts:5 (Prisma Client Singleton)
            └─► PostgreSQL Database (src/prisma/schema.prisma:1)
```

## Layer Responsibilities
1. **Bootstrap & Middleware**: `src/main.ts:13-19` configures CORS, JSON parsing, URL encoding, static assets, and global error handling (`src/main.ts:26`).
2. **Routing & Dispatch**: `src/app/routes/routes.ts:7-13` aggregates domain sub-routers into `/api`.
3. **Domain Controllers**: Extract query/body params, apply auth guards (`src/app/routes/auth/auth.ts:14`), and delegate to services.
4. **Domain Services**: Business logic, slug generation, cascading operations, and database access via Prisma (`src/app/routes/article/article.service.ts:20`).
5. **Data Access**: `src/prisma/prisma-client.ts:5-23` maintains persistent database pooling.
