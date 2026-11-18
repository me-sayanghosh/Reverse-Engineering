# 03 - API Surface & Data Models: node-express-realworld-example-app

## REST API Endpoints
All endpoints mounted at `/api` (`src/app/routes/routes.ts:13`):
- `POST /api/users/login`: Authenticate existing user (`src/app/routes/auth/auth.controller.ts:35`).
- `POST /api/users`: Register new user account (`src/app/routes/auth/auth.controller.ts:15`).
- `GET /api/user`: Get current user [Auth] (`src/app/routes/auth/auth.controller.ts:45`).
- `PUT /api/user`: Update current user profile [Auth] (`src/app/routes/auth/auth.controller.ts:55`).
- `GET /api/profiles/:username`: Retrieve user profile (`src/app/routes/profile/profile.controller.ts:15`).
- `POST /api/profiles/:username/follow`: Follow user [Auth] (`src/app/routes/profile/profile.controller.ts:25`).
- `GET /api/articles`: Query and filter articles list (`src/app/routes/article/article.controller.ts:25`).
- `POST /api/articles`: Create article [Auth] (`src/app/routes/article/article.controller.ts:45`).
- `GET /api/tags`: List all unique tags (`src/app/routes/tag/tag.controller.ts:10`).

## Prisma Data Schema
- **Article** (`src/prisma/schema.prisma:11`): id, slug, title, description, body, authorId, tagList.
- **Comment** (`src/prisma/schema.prisma:26`): id, body, articleId, authorId, createdAt.
- **Tag** (`src/prisma/schema.prisma:37`): id, name, articles.
- **User** (`src/prisma/schema.prisma:43`): id, email, username, password, bio, image.
