# Architecture — FlashLang

## System Overview
FlashLang is a three-tier application: a React SPA communicates with a NestJS REST API
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
│                     NestJS API Server :3000                     │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │   Auth   │  │ Languages│  │ Sets +   │  │   Learning    │  │
│  │  Module  │  │  Module  │  │  Cards   │  │    Module     │  │
│  └──────────┘  └──────────┘  │  Module  │  │  (SM-2 core)  │  │
│                               └──────────┘  └───────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    TypeORM (Data Access)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      MySQL 8         │
                    │  (local / RDS)       │
                    └──────────────────────┘
```

## NestJS Module Map
```
AppModule
├── AuthModule          register, login, refresh, logout; JwtStrategy; JwtAuthGuard (global)
├── UsersModule         UserEntity, UsersRepository, UsersService (used by AuthModule)
├── LanguagesModule     LanguageEntity, GET /languages (public)
├── FlashcardSetsModule FlashcardSet CRUD, ownership enforcement, card_count denormalization
├── FlashcardsModule    Flashcard CRUD, bulk import, SR fields on entity
├── LearningModule      Session create/review/complete, SpacedRepetitionService
└── StatsModule         Overview counters, streak calc, daily progress query
```

## Layers & Responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| Controllers | `src/*/\*.controller.ts` | Parse HTTP, validate DTO via pipe, call service, return response DTO |
| Services | `src/*/\*.service.ts` | All business logic; orchestrate repositories; throw HTTP exceptions |
| Repositories | `src/*/\*.repository.ts` | TypeORM queries only; no business logic |
| Entities | `src/*/entities/\*.entity.ts` | TypeORM class = DB table; column name mappings |
| DTOs | `src/*/dto/\*.dto.ts` | Input/output shapes with class-validator decorators |
| Guards | `src/auth/guards/` | JwtAuthGuard (global) + @Public() bypass |

## Data Flow — Standard Request
1. HTTP → NestJS router
2. `JwtAuthGuard` validates Bearer token → attaches `{ userId, email }` to `req.user`
3. Controller pipe validates + transforms request body DTO
4. Controller calls service method with typed args
5. Service applies business logic, calls one or more repositories
6. Repository executes TypeORM query, returns entity
7. Service maps entity → response DTO (never return raw entity)
8. Controller returns response DTO → NestJS serialises to JSON

## Data Flow — Learning Session Review
```
POST /learning/sessions/:id/reviews
  → LearningController.submitReview(sessionId, userId, dto)
    → LearningService.submitReview(...)
      → Verify session is active + owned by user
      → Fetch Flashcard entity
      → SpacedRepetitionService.calculateNext(card, dto.result)  [pure, no DB]
      → CardRepository.save(updated SR fields)
      → ReviewResultRepository.insert(row)
      → LearningSessionRepository.incrementCounters(sessionId, result)
      → Return { cardId, nextReviewAt, intervalDays, easeFactor }
```

## Spaced Repetition — SM-2 Simplified
```
calculateNext(card, result):
  if result === 'remembered':
    interval = card.repetitions === 0 ? 1
             : card.repetitions === 1 ? 6
             : Math.round(card.intervalDays * card.easeFactor)
    easeFactor = Math.min(2.5, card.easeFactor + 0.1)
    repetitions = card.repetitions + 1
  else:
    interval = 1
    easeFactor = Math.max(1.3, card.easeFactor - 0.2)
    repetitions = 0
  nextReviewAt = addDays(new Date(), interval)
  return { intervalDays: interval, easeFactor, repetitions, nextReviewAt }
```

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| NestJS over Express | Built-in DI, modules, guards, interceptors, OpenAPI — far less boilerplate |
| TypeORM with `synchronize: false` | Schema.sql is the authoritative source of truth; no accidental migrations |
| `@Column({ select: false })` on passwordHash | Defense-in-depth: can't accidentally leak the hash in any query |
| JWT in-memory (Zustand) | Prevents XSS theft; HttpOnly refresh cookie restores session on reload |
| Refresh token rotation | Each refresh invalidates the old token — bounded damage window if stolen |
| SM-2 as pure service | No DB dependency → trivially unit testable; portable to mobile |
| Composite index `(set_id, next_review_at)` | "Due cards" query is the hottest path; must be O(log n) not O(n) |
| `card_count` denormalized on sets | Avoids COUNT subquery on every deck list; maintained by service layer |
| `/api` Vite proxy in dev | No CORS preflight complexity during development |

## Security Model
- Passwords: bcrypt cost factor 12
- Access token: RS256 signed (or HS256), 15-minute expiry, Authorization header
- Refresh token: 7-day expiry, HttpOnly + Secure + SameSite=Strict cookie, stored as bcrypt hash in DB
- Refresh token rotation: old token deleted on use; replay attack is detected (token not in DB)
- Ownership: every service method takes `userId` from JWT and filters queries by it (no IDOR)
- CORS: restricted to `FRONTEND_URL` env var with `credentials: true`

## Out of Scope (v1)
- Audio pronunciation
- Image attachments on cards
- Social/sharing features
- Real-time multiplayer
- Offline-first mobile caching
