# 06 - Observability & Operations: node-express-realworld-example-app

## Operations & Deployment
- **Dockerfile**: Multi-stage production container build (`Dockerfile:1-24`).
- **Database Migrations**: Prisma migration SQL directory (`src/prisma/migrations/20210924225358_initial/migration.sql:1`).
- **Database Seed**: Seed script for initial fixtures (`src/prisma/seed.ts:1-66`).
- **Health Check**: Root endpoint returns API status (`src/main.ts:21-23`).
