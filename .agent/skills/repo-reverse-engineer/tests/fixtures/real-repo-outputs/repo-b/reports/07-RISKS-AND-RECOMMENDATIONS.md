# 07 - Risks & Recommendations: node-express-realworld-example-app

## Security Findings
1. **Fallback Secret**: Hardcoded secret fallback `superSecret` in `src/app/routes/auth/auth.ts:16`. Enforce mandatory process.env validation.
2. **Error Information Leakage**: Error middleware returns error name/details to client (`src/main.ts:35`).

## Architectural Recommendations
1. Upgrade Prisma to latest v5 engine.
2. Implement rate limiting on `/api/users/login` endpoint (`src/app/routes/auth/auth.controller.ts:35`).
