# Architecture — FlashLang

## System Overview
FlashLang is a three-tier application: a React SPA communicates with a FastAPI REST API
which persists data in MySQL 8. JWT access tokens travel in the Authorization header;
refresh tokens live in an HttpOnly cookie, enabling silent session restoration without
localStorage. The same API serves the web client and will serve future mobile clients
without modification.

## Component Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENTS                                │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐  │
│  │   React SPA    │   │ React Native   │   │ Swift/Kotlin   │  │
│  │  (browser)     │   │  (future)      │   │  (future)      │  │
│  └───────┬────────┘   └───────┬────────┘   └───────┬────────┘  │
└──────────┼────────────────────┼────────────────────┼───────────┘
           │  HTTPS REST        │  HTTPS REST         │
           ▼                    ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI API Server :8000                       │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │   auth/  │  │languages/│  │ sets/ +  │  │  learning/    │  │
│  │  router  │  │  router  │  │ cards/   │  │  router       │  │
│  └──────────┘  └──────────┘  │ routers  │  │ (SM-2 core)   │  │
│                               └──────────┘  └───────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              SQLAlchemy ORM (Data Access)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      MySQL 8         │
                    │  (local / RDS)       │
                    └──────────────────────┘
```

## Router Map
```
main.py (FastAPI app)
├── /auth        auth/router.py       register, login, refresh, logout
├── /languages   languages/router.py  GET /languages (public)
├── /sets        flashcard_sets/      Set CRUD, ownership enforcement, card_count denorm
├── /cards       flashcards/          Card CRUD, bulk import, Excel import, examples
├── /learning    learning/            Session create/review/complete, SM-2
└── /stats       stats/               Overview counters, streak calc, daily progress
```

## Layers & Responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| Routers | `app/*/router.py` | Parse HTTP, validate via Pydantic, call service, return response schema |
| Services | `app/*/service.py` | All business logic; SQLAlchemy Session queries; raise HTTPException |
| Schemas | `app/*/schemas.py` | Pydantic v2 models for request/response; inherits CamelModel for camelCase |
| Models | `app/models.py` | SQLAlchemy ORM — single source of truth for DB shape |
| Dependencies | `app/dependencies.py` | `get_current_user` (JWT → User), `get_db` (Session injection) |
| Base schema | `app/base_schema.py` | `CamelModel` — `model_config` with `populate_by_name=True`, `serialize_by_alias=True` |

No separate repository layer — services query the DB directly via `Session`.

## Data Flow — Standard Request
1. HTTP → FastAPI router
2. `Depends(get_current_user)` decodes Bearer token → injects `models.User` into route handler
3. `Depends(get_db)` injects `Session` into route handler
4. Pydantic validates + parses request body into schema
5. Router calls service function with typed args (user, db, schema)
6. Service applies business logic, queries DB via `db.query(...)` / `db.add()` / `db.commit()`
7. Service returns ORM model or response schema
8. Router returns Pydantic response schema → FastAPI serialises to camelCase JSON

## Data Flow — Learning Session Review
```
POST /learning/sessions/{session_id}/reviews
  → learning/router.py: submit_review(session_id, dto, user, db)
    → learning/service.py: submit_review(db, session_id, user.id, dto)
      → Verify session is active + owned by user
      → Fetch Flashcard from DB
      → spaced_repetition.calculate_next(card, dto.result)  [pure, no DB]
      → Update card SR fields + db.commit()
      → Insert ReviewResult row
      → Increment session counters + db.commit()
      → Return ReviewResultResponse (card_id, next_review_at, interval_days, ease_factor)
```

## Spaced Repetition — SM-2 Simplified
Lives in `backend/app/learning/spaced_repetition.py`. Pure function — no DB dependency.

```
calculate_next(card, result):
  if result == 'remembered':
    interval = 1               if card.repetitions == 0
             = 6               if card.repetitions == 1
             = round(card.interval_days * card.ease_factor)  otherwise
    ease_factor = min(2.5, card.ease_factor + 0.1)
    repetitions = card.repetitions + 1
  else:
    interval    = 1
    ease_factor = max(1.3, card.ease_factor - 0.2)
    repetitions = 0
  next_review_at = now() + interval days
```

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| FastAPI over Flask/Django | Built-in async, automatic OpenAPI, Pydantic integration, speed |
| SQLAlchemy with Alembic | Migration history, auto-generate from models, no accidental schema drift |
| `app/models.py` as single source of truth | All schema changes flow through here → Alembic → DB |
| No repository layer | Services are thin; adding a repo layer would be indirection without benefit |
| `get_current_user` FastAPI dependency | Reusable, composable; injected only where auth is required |
| CamelModel base schema | Frontend expects camelCase; `serialize_by_alias=True` handles all serialization automatically |
| JWT in-memory (Zustand) | Prevents XSS theft; HttpOnly refresh cookie restores session on reload |
| Refresh token rotation | Each refresh deletes old token + issues new one — bounded damage if stolen |
| Refresh token stored as bcrypt hash | Raw token never persisted; replay attack detected when hash not found |
| SM-2 as pure function | No DB dependency → trivially unit testable; portable to mobile |
| Composite index `(set_id, next_review_at)` | "Due cards" query is the hottest path; must be O(log n) not O(n) |
| `card_count` denormalized on sets | Avoids COUNT subquery on every deck list; maintained by service layer |
| `/api` Vite proxy in dev | No CORS preflight complexity during development |

## Security Model
- Passwords: bcrypt (rounds configured via `BCRYPT_ROUNDS` env var, default 12)
- Access token: HS256 signed, 15-minute expiry, Authorization Bearer header
- Refresh token: HS256 signed, 7-day expiry, HttpOnly + SameSite=Strict cookie; stored as bcrypt hash in `refresh_tokens` table
- Refresh token rotation: old token deleted on use; replay attack detected (hash not in DB)
- Only 1 refresh token per user — previous token deleted on new login
- Ownership: every service method receives `user.id` from JWT and filters all DB queries by it (no IDOR)
- CORS: restricted to `FRONTEND_URL` env var with `credentials: true`

## Out of Scope (v1)
- Audio pronunciation
- Image attachments on cards
- Social/sharing features
- Real-time multiplayer
- Offline-first mobile caching
