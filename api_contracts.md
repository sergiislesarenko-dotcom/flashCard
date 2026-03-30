# API Contracts — FlashLang

Base URL: `https://api.flashlang.com/v1` (dev: `http://localhost:3000`)
Auth: `Authorization: Bearer <accessToken>` on all protected routes
Content-Type: `application/json`
All timestamps: ISO 8601 UTC strings

---

## Standard Error Envelope
All error responses use this shape:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [{ "field": "email", "issue": "must be a valid email address" }]
  }
}
```
**Common error codes:** `VALIDATION_ERROR` (400), `UNAUTHORIZED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404), `CONFLICT` (409), `INTERNAL_ERROR` (500)

---

## Standard Pagination
All list endpoints accept `?page=1&pageSize=20` and return:
```json
{
  "data": [...],
  "pagination": { "page": 1, "pageSize": 20, "total": 143 }
}
```

---

## Auth — Public Routes

### POST /auth/register
```json
// Request
{ "email": "alice@example.com", "password": "min8chars", "displayName": "Alice" }

// Response 201
{ "id": 1, "email": "alice@example.com", "displayName": "Alice", "createdAt": "2026-03-26T10:00:00Z" }
```
Errors: `400 VALIDATION_ERROR`, `409 CONFLICT` (email already registered)

---

### POST /auth/login
```json
// Request
{ "email": "alice@example.com", "password": "secret" }

// Response 200
// Also sets: Set-Cookie: refresh_token=<token>; HttpOnly; Secure; SameSite=Strict; Path=/auth/refresh; Max-Age=604800
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "expiresIn": 900,
  "user": { "id": 1, "email": "alice@example.com", "displayName": "Alice" }
}
```
Errors: `401 UNAUTHORIZED`

---

### POST /auth/refresh
Uses the `refresh_token` HttpOnly cookie. No request body.
```json
// Response 200
// Rotates cookie: issues new refresh_token cookie, invalidates old one
{
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "expiresIn": 900
}
```
Errors: `401 UNAUTHORIZED` (missing/expired/invalid/already-used token)

---

### POST /auth/logout — Protected
No request body.
```
// Response 204 — clears refresh_token cookie
```

---

## Languages — Protected

### GET /languages
```json
// Response 200
[
  { "id": 1, "code": "ru", "name": "Russian",  "flag": "🇷🇺" },
  { "id": 2, "code": "de", "name": "German",   "flag": "🇩🇪" },
  { "id": 3, "code": "es", "name": "Spanish",  "flag": "🇪🇸" },
  { "id": 4, "code": "fr", "name": "French",   "flag": "🇫🇷" },
  { "id": 5, "code": "ja", "name": "Japanese", "flag": "🇯🇵" },
  { "id": 6, "code": "zh", "name": "Chinese",  "flag": "🇨🇳" },
  { "id": 7, "code": "it", "name": "Italian",  "flag": "🇮🇹" },
  { "id": 8, "code": "pt", "name": "Portuguese","flag": "🇵🇹" }
]
```

---

## Flashcard Sets — Protected

### GET /sets
```json
// Query: ?page=1&pageSize=20
// Response 200
{
  "data": [
    {
      "id": 1,
      "name": "Basic Greetings",
      "language": { "id": 2, "code": "de", "name": "German", "flag": "🇩🇪" },
      "cardCount": 12,
      "dueCount": 4,
      "createdAt": "2026-01-15T10:00:00Z"
    }
  ],
  "pagination": { "page": 1, "pageSize": 20, "total": 3 }
}
```

### POST /sets
```json
// Request
{ "name": "Basic Greetings", "languageId": 2, "description": "Common phrases" }

// Response 201
{ "id": 1, "name": "Basic Greetings", "languageId": 2, "description": "Common phrases",
  "cardCount": 0, "createdAt": "2026-03-26T10:00:00Z" }
```
Errors: `400 VALIDATION_ERROR`

### GET /sets/:id
```json
// Response 200 — set object with cards array
{
  "id": 1,
  "name": "Basic Greetings",
  "language": { "id": 2, "code": "de", "name": "German" },
  "description": "Common phrases",
  "cardCount": 12,
  "cards": [
    { "id": 101, "front": "Привет", "back": "Hallo", "nextReviewAt": "2026-03-27T00:00:00Z",
      "easeFactor": 2.5, "intervalDays": 1, "repetitions": 0 }
  ]
}
```
Errors: `404 NOT_FOUND`, `403 FORBIDDEN`

### PATCH /sets/:id
```json
// Request (all fields optional)
{ "name": "Updated Name", "description": "Updated description" }
// Response 200 — updated set object (without cards array)
```
Errors: `404`, `403`, `400`

### DELETE /sets/:id
```
// Response 204
```
Errors: `404`, `403`

---

## Flashcards — Protected

### GET /cards
```json
// Query: ?setId=1&page=1&pageSize=50
// Response 200
{
  "data": [
    { "id": 101, "front": "Привет", "back": "Hallo", "setId": 1,
      "nextReviewAt": "2026-03-27T00:00:00Z", "easeFactor": 2.5,
      "intervalDays": 1, "repetitions": 0 }
  ],
  "pagination": { "page": 1, "pageSize": 50, "total": 12 }
}
```
Errors: `400` (missing setId), `403` (not your set)

### POST /cards
```json
// Request
{ "setId": 1, "front": "Привет", "back": "Hallo" }
// Response 201
{ "id": 101, "setId": 1, "front": "Привет", "back": "Hallo",
  "nextReviewAt": "<now>", "easeFactor": 2.5, "intervalDays": 1, "repetitions": 0 }
```

### PATCH /cards/:id
```json
// Request (partial — only front/back)
{ "front": "Привет!", "back": "Hallo!" }
// Response 200 — updated card
```
Errors: `404`, `403`

### DELETE /cards/:id
```
// Response 204
```

### POST /cards/import
```json
// Request
{
  "setId": 1,
  "cards": [
    { "front": "Да",  "back": "Ja" },
    { "front": "Нет", "back": "Nein" }
  ]
}
// Response 201
{ "imported": 2, "skipped": 0 }
```
Errors: `400`, `403` (not your set)

---

## Learning Sessions — Protected

### POST /learning/sessions
Start a new session. Backend selects N cards due for review from the set.
```json
// Request
{ "setId": 1, "cardCount": 20 }

// Response 201
{
  "sessionId": 42,
  "setId": 1,
  "cards": [
    { "id": 101, "front": "Привет" }
  ],
  "totalCards": 12,
  "startedAt": "2026-03-26T10:00:00Z"
}
```
Note: `back` is NOT included — client requests flip action via store state, not API.

### GET /learning/sessions/:id
```json
// Response 200
{
  "sessionId": 42,
  "setId": 1,
  "status": "active",
  "totalCards": 12,
  "cardsReviewed": 5,
  "cardsRemembered": 4,
  "startedAt": "2026-03-26T10:00:00Z",
  "completedAt": null
}
```

### POST /learning/sessions/:id/reviews
Submit result for one card. Updates card SR fields. Returns new SR values.
```json
// Request
{ "cardId": 101, "result": "remembered" }
// result must be "remembered" | "repeat"

// Response 200
{
  "cardId": 101,
  "result": "remembered",
  "nextReviewAt": "2026-04-01T00:00:00Z",
  "intervalDays": 6,
  "easeFactor": 2.6,
  "repetitions": 2
}
```
Errors: `404` (session or card not found), `403` (not your session), `409` (card already reviewed in this session)

### POST /learning/sessions/:id/complete
Mark session as finished.
```json
// Response 200
{
  "sessionId": 42,
  "status": "completed",
  "totalCards": 12,
  "cardsReviewed": 12,
  "cardsRemembered": 10,
  "repeatCount": 2,
  "accuracyPercent": 83,
  "completedAt": "2026-03-26T10:25:00Z"
}
```

---

## Statistics — Protected

### GET /stats/overview
```json
// Response 200
{
  "totalSets": 3,
  "totalCards": 120,
  "dueToday": 14,
  "sessionsCompleted": 23,
  "streakDays": 5,
  "averageAccuracy": 78
}
```

### GET /stats/progress
```json
// Query: ?from=2026-03-01&to=2026-03-26  (ISO date strings, inclusive)
// Response 200
{
  "data": [
    {
      "date": "2026-03-26",
      "sessionsCompleted": 1,
      "cardsReviewed": 20,
      "cardsRemembered": 17
    }
  ]
}
```
