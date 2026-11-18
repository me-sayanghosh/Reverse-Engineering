# 05 - Key Algorithms: node-express-realworld-example-app

## 1. Unique Slug Generation
- Converts article titles into URL slugs using `slug` package (`src/app/routes/article/article.service.ts:50`).
- Appends randomized or numerical suffixes on collision (`src/app/routes/article/article.service.ts:55`).

## 2. Follower & Favorite Graph Queries
- Implements self-referential many-to-many user relations (`src/prisma/schema.prisma:50-51`).
- Queries follower state dynamically during article mapping (`src/app/routes/article/author.mapper.ts:5`).
