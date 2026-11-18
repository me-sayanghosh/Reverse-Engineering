# 04 - Dependency Health: node-express-realworld-example-app

## Key Production Dependencies
- `@prisma/client`: 3.14.0 - Database ORM query engine (`package.json:20`).
- `express`: 4.18.1 - Core web routing engine (`package.json:22`).
- `express-jwt`: 7.7.5 - JWT validation middleware (`package.json:23`).
- `jsonwebtoken`: 8.5.1 - Token signing and verification (`package.json:24`).
- `slug`: 5.3.0 - URL-safe string conversion (`package.json:28`).

## Vulnerability Surface
- `jsonwebtoken` version 8.x is pinned; should be audited against known algorithm confusion vulnerabilities.
