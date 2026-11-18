# 08 - Clean-Room Rebuild Blueprint: demo-app

## System Architecture Blueprint
The demo application is a minimal Node.js/Express REST API backed by MongoDB via Mongoose. It exposes user authentication stubs and authenticated CRUD operations over item resources.

```
Clients (HTTP)
      │
      ▼
Server Bootstrap (`src/server.js:5`)
      │
      ▼
Express Application (`src/app.js:5`)
      ├─ Middleware: JSON Body Parser (`src/app.js:7`)
      │
      ├─ Auth Router (`src/routes/auth.js:2` mounted at `src/app.js:9`)
      │     ├─ POST /auth/login (`src/routes/auth.js:4`)
      │     └─ POST /auth/register (`src/routes/auth.js:8`)
      │
      └─ Items Router (`src/routes/items.js:5` mounted at `src/app.js:10`)
            ├─ GET /items (`src/routes/items.js:7`)
            ├─ POST /items [Auth Guard] (`src/routes/items.js:12`, `src/middleware/auth.js:3`)
            ├─ DELETE /items/:id [Auth Guard] (`src/routes/items.js:18`, `src/middleware/auth.js:3`)
            └─ Item Model (`src/models/item.js:3`)
```

---

## Rebuild Milestones & Phased Plan

### Milestone 1: Project Scaffold & Server Bootstrap
- **Objective**: Initialize package configuration, runtime scripts, and HTTP server bootstrap.
- **Key Deliverables**:
  - `package.json`: Dependency manifest with Express, Mongoose, and JWT (`package.json:10-15`).
  - `.env.example`: Environment configuration template for PORT and secrets (`.env.example:1-3`).
  - `src/app.js`: Express application initialization and JSON parsing (`src/app.js:1-7`).
  - `src/server.js`: HTTP listener binding to PORT (`src/server.js:1-7`).
- **Pseudocode**:
  ```javascript
  const express = require('express');
  const app = express();
  app.use(express.json());
  module.exports = app;
  ```
- **Implementation Prompt for Coding Agent**:
  > "Scaffold a Node.js project. Create a `package.json` with dependencies `express`, `mongoose`, `jsonwebtoken`, and `dotenv`. Create `.env.example` defining PORT, MONGODB_URI, and JWT_SECRET. In `src/app.js`, create and export an Express application with `express.json()` middleware. In `src/server.js`, import `src/app.js` and call `app.listen(process.env.PORT || 3000)`."

---

### Milestone 2: Schema Modeling & Persistence
- **Objective**: Implement Mongoose document models for persisted resources.
- **Key Deliverables**:
  - `src/models/item.js`: Mongoose schema defining `title`, `price`, `description`, `owner`, and `createdAt` (`src/models/item.js:3-9`).
- **Pseudocode**:
  ```javascript
  const itemSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: String,
    price: { type: Number, required: true },
    owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    createdAt: { type: Date, default: Date.now },
  });
  ```
- **Implementation Prompt for Coding Agent**:
  > "Implement the data model in `src/models/item.js`. Use Mongoose to define an Item schema with required string `title`, optional string `description`, required number `price`, an `owner` ObjectId reference to 'User', and a `createdAt` date defaulting to now. Export the compiled model."

---

### Milestone 3: Authentication Middleware & Auth Routes
- **Objective**: Secure routes with JWT verification and establish authentication entrypoints.
- **Key Deliverables**:
  - `src/middleware/auth.js`: Bearer token inspection and verification middleware (`src/middleware/auth.js:3-16`).
  - `src/routes/auth.js`: Auth router exposing login and registration routes (`src/routes/auth.js:4-10`).
- **Pseudocode**:
  ```javascript
  function requireAuth(req, res, next) {
    const header = req.headers.authorization;
    if (!header || !header.startsWith('Bearer ')) return res.status(401).json({ error: 'Unauthorized' });
    const token = header.split(' ')[1];
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  }
  ```
- **Implementation Prompt for Coding Agent**:
  > "Implement authentication in `src/middleware/auth.js` and `src/routes/auth.js`. The middleware should verify the Authorization Bearer token using jsonwebtoken and attach `req.user`, responding with 401 on error. `src/routes/auth.js` should export an Express router with `POST /login` returning `{ token }` and `POST /register` returning status 201."

---

### Milestone 4: Items API Endpoints & Route Mounting
- **Objective**: Build CRUD route handlers for items and mount routers onto the main Express application.
- **Key Deliverables**:
  - `src/routes/items.js`: Route handlers for GET, POST, and DELETE on `/items` (`src/routes/items.js:7-21`).
  - `src/app.js`: Mount routers at `/auth` and `/items` (`src/app.js:9-10`).
- **Pseudocode**:
  ```javascript
  router.get('/', async (req, res) => res.json(await Item.find({})));
  router.post('/', requireAuth, async (req, res) => res.status(201).json(await new Item(req.body).save()));
  router.delete('/:id', requireAuth, async (req, res) => {
    await Item.findByIdAndDelete(req.params.id);
    res.status(204).send();
  });
  ```
- **Implementation Prompt for Coding Agent**:
  > "Implement the items resource in `src/routes/items.js`. Include `GET /` to list all items, `POST /` with `requireAuth` to persist a new item, and `DELETE /:id` with `requireAuth` to delete an item. Mount `src/routes/auth.js` at `/auth` and `src/routes/items.js` at `/items` inside `src/app.js`."

---

## Critical Path & Complexity Pitfalls
1. **Token Secret Fallback**: Ensure production deployment verifies that `JWT_SECRET` is present in the environment rather than relying on a fallback string (`src/middleware/auth.js:10`).
2. **Missing Database Connection Bootstrap**: In production, ensure `mongoose.connect(process.env.MONGODB_URI)` is awaited before accepting traffic in `src/server.js:5`.
3. **Missing Input Validation**: Incoming `req.body` values should be validated with a schema validator prior to `Item` persistence in `src/routes/items.js:13`.
