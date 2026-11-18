# 02 - Core Data Flows: node-express-realworld-example-app

## 1. User Registration & Authentication Flow
1. Client POST to `/api/users` (`src/app/routes/auth/auth.controller.ts:15`).
2. Validation checks for unique email and username (`src/app/routes/auth/auth.service.ts:25`).
3. Password hashed using bcrypt/crypto helper (`src/app/routes/auth/auth.service.ts:30`).
4. User record persisted in PostgreSQL (`src/prisma/schema.prisma:43`).
5. Signed JWT token returned in JSON response (`src/app/routes/auth/token.utils.ts:4`).

## 2. Article Creation with Tags & Slug Flow
1. Client sends authenticated POST to `/api/articles` (`src/app/routes/article/article.controller.ts:45`).
2. Auth middleware verifies JWT token (`src/app/routes/auth/auth.ts:15`).
3. Title slug generated with collision resolution (`src/app/routes/article/article.service.ts:50`).
4. Tags upserted and linked via Prisma relation (`src/prisma/schema.prisma:19`).
5. Article persisted and returned with author profile (`src/app/routes/article/article.mapper.ts:4`).
