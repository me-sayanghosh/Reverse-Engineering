# 08 - Clean-Room Rebuild Blueprint: node-express-realworld-example-app

## System Architecture Blueprint
A clean-room implementation of the RealWorld backend using Express, TypeScript, and Prisma ORM.

```
Clients
   │
   ▼
src/main.ts:7 (Express App)
   ├─► src/app/routes/auth/auth.ts:14 (JWT Middleware)
   ├─► src/app/routes/routes.ts:13 (/api Routes)
   │     ├─► User & Auth Modules (src/app/routes/auth/auth.service.ts:1)
   │     ├─► Article Module (src/app/routes/article/article.service.ts:1)
   │     ├─► Profile Module (src/app/routes/profile/profile.service.ts:1)
   │     └─► Tag Module (src/app/routes/tag/tag.service.ts:1)
   │
   └─► Prisma Datastore Layer (src/prisma/schema.prisma:11)
```

---

## Rebuild Milestones & Phased Plan

### Milestone 1: Core Express & Prisma Database Setup
- **Objective**: Scaffold TypeScript project, configure Express server, and establish Prisma PostgreSQL connection.
- **Key Deliverables**:
  - `package.json`: Dependencies for express, prisma, dotenv (`package.json:20-28`).
  - `src/main.ts`: Express application initialization with CORS and JSON body-parsing (`src/main.ts:7-19`).
  - `src/prisma/schema.prisma`: Database connection and client generation setup (`src/prisma/schema.prisma:1-9`).
  - `src/prisma/prisma-client.ts`: Singleton PrismaClient instance (`src/prisma/prisma-client.ts:5-23`).
- **Pseudocode**:
  ```typescript
  const app = express();
  app.use(cors());
  app.use(bodyParser.json());
  ```
- **Implementation Prompt for Coding Agent**:
  > "Scaffold a TypeScript Express application. Set up Prisma with PostgreSQL provider in `src/prisma/schema.prisma`. Create a singleton Prisma client in `src/prisma/prisma-client.ts`. Initialize Express in `src/main.ts` with CORS, bodyParser.json, and a health check route on `GET /`."

---

### Milestone 2: User Authentication & JWT Middleware
- **Objective**: Implement user registration, login, credential encryption, and token verification.
- **Key Deliverables**:
  - `src/prisma/schema.prisma`: User model with email, username, password, bio, image (`src/prisma/schema.prisma:43-55`).
  - `src/app/routes/auth/auth.ts`: Middleware extracting Bearer/Token headers (`src/app/routes/auth/auth.ts:4-26`).
  - `src/app/routes/auth/auth.service.ts`: Registration and login business logic (`src/app/routes/auth/auth.service.ts:20-60`).
  - `src/app/routes/auth/auth.controller.ts`: Endpoints for `/api/users` and `/api/users/login` (`src/app/routes/auth/auth.controller.ts:15-40`).
- **Implementation Prompt for Coding Agent**:
  > "Implement authentication. Add User model to `src/prisma/schema.prisma`. In `src/app/routes/auth/auth.ts`, create JWT middleware that parses both Bearer and Token header formats. Implement `src/app/routes/auth/auth.service.ts` for user registration with bcrypt password hashing and token issuance. Wire routes in `src/app/routes/auth/auth.controller.ts`."

---

### Milestone 3: Article Management & Tagging System
- **Objective**: Implement article authoring, unique slug generation, tag relationships, and comment threads.
- **Key Deliverables**:
  - `src/prisma/schema.prisma`: Article, Comment, and Tag models (`src/prisma/schema.prisma:11-40`).
  - `src/app/routes/article/article.service.ts`: Article creation, slug generation, and query filtering (`src/app/routes/article/article.service.ts:50-100`).
  - `src/app/routes/article/article.controller.ts`: Handlers for GET, POST, PUT, DELETE `/api/articles` (`src/app/routes/article/article.controller.ts:25-70`).
  - `src/app/routes/tag/tag.controller.ts`: Handler for `GET /api/tags` (`src/app/routes/tag/tag.controller.ts:10-20`).
- **Implementation Prompt for Coding Agent**:
  > "Implement the articles and tags domain. Add Article, Comment, and Tag models in Prisma schema. In `src/app/routes/article/article.service.ts`, implement article creation with slug generation and tag relation linking. Implement `src/app/routes/article/article.controller.ts` supporting full CRUD operations, and `src/app/routes/tag/tag.controller.ts` returning distinct tags."

---

### Milestone 4: Social Graph & End-to-End Integration
- **Objective**: Implement user profile retrieval, follow/unfollow relations, article favorites, and mount all routes.
- **Key Deliverables**:
  - `src/app/routes/profile/profile.controller.ts`: Follow and unfollow endpoints (`src/app/routes/profile/profile.controller.ts:15-35`).
  - `src/app/routes/routes.ts`: Central router mounting `/api` endpoints (`src/app/routes/routes.ts:7-13`).
  - `src/main.ts`: Mount api router into Express app (`src/main.ts:16`).
- **Implementation Prompt for Coding Agent**:
  > "Implement profile and social follow mechanics. Create `src/app/routes/profile/profile.controller.ts` and service to manage following/unfollowing users and querying profile states. In `src/app/routes/routes.ts`, mount auth, article, profile, and tag controllers under `/api`. Mount the router into `src/main.ts` and write integration tests."

---

## Critical Path & Complexity Pitfalls
1. **Secret Environment Enforcement**: Throw on startup if `JWT_SECRET` is unset (`src/app/routes/auth/auth.ts:16`).
2. **Database Cascade Deletions**: Configure `onDelete: Cascade` in Prisma schema to prevent orphaned records (`src/prisma/schema.prisma:20`).
3. **Many-to-Many Prisma Relations**: Use explicit junction mappings if custom metadata on favorites is required (`src/prisma/schema.prisma:22`).
