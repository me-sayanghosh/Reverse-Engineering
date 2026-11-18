# 00 - Executive Summary: demo-app

## Repository Overview
- **Repository URL / Path**: `tests/fixtures/demo-app`
- **Analyzed Commit / Ref**: `local-working-tree` (Branch: `dev`)
- **Primary Language & Stack**: Node.js / JavaScript (Express 4.18, Mongoose 8.0)
- **License**: none detected (Internal Demo)
- **Mode**: standard | **Target Audience**: senior

## Purpose & Problem Solved
The `demo-app` service is a lightweight RESTful API designed for managing inventory or catalog items with role-based JWT authentication and MongoDB persistence.

## High-Level Architecture & Key Components
- **Core Architecture Style**: Layered Express REST API
- **Primary Subsystems**:
  1. `HTTP Routing & Application Core`: Orchestrated in `src/app.js:6-12`.
  2. `Authentication Middleware`: JWT verification implemented in `src/middleware/auth.js:3-17`.
  3. `Data Persistence`: Mongoose item schema defined in `src/models/item.js:3-11`.

## Top 5 Things to Know Before Touching This Codebase
1. **Server Entrypoint**: Application bootstrap listens on port 3000 via `src/server.js:5`.
2. **Modular Routers**: API endpoints split between `/auth` (`src/app.js:10`) and `/items` (`src/app.js:11`).
3. **Protected Mutation Routes**: Mutation handlers (`POST`, `DELETE`) enforce auth middleware at `src/routes/items.js:12` and `src/routes/items.js:18`.
4. **JWT Verification Mechanism**: Token extraction validates the `Bearer` header at `src/middleware/auth.js:4-7`.
5. **Item Schema Constraints**: Title and price are mandatory fields defined at `src/models/item.js:4-6`.

## Quick-Start Commands
- **Install Dependencies**: `npm install`
- **Run Locally**: `npm start`
- **Execute Tests**: `npm test`
