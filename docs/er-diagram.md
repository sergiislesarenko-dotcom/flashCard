# Entity Relationship Diagram — FlashLang

## Tables and Relationships

```
users
 ├── id (PK)
 ├── email (UNIQUE)
 ├── display_name
 ├── password_hash
 ├── created_at
 └── updated_at
      │
      ├──< refresh_tokens (user_id FK, CASCADE DELETE)
      │     ├── id (PK)
      │     ├── token_hash (UNIQUE)
      │     └── expires_at
      │
      ├──< flashcard_sets (user_id FK, CASCADE DELETE)
      │     ├── id (PK)
      │     ├── language_id (FK → languages)
      │     ├── name
      │     ├── description
      │     ├── card_count  [denormalized]
      │     │
      │     └──< flashcards (set_id FK, CASCADE DELETE)
      │           ├── id (PK)
      │           ├── front
      │           ├── back
      │           ├── ease_factor     [SR field, default 2.50]
      │           ├── interval_days   [SR field, default 1]
      │           ├── repetitions     [SR field, default 0]
      │           └── next_review_at  [SR field, default NOW()]
      │
      └──< learning_sessions (user_id FK, CASCADE DELETE)
            ├── id (PK)
            ├── set_id (FK → flashcard_sets, CASCADE DELETE)
            ├── status  ENUM: active | completed | abandoned
            ├── total_cards
            ├── cards_reviewed
            ├── cards_remembered
            ├── started_at
            ├── completed_at
            │
            └──< review_results (session_id FK, CASCADE DELETE)
                  ├── id (PK)
                  ├── card_id (FK → flashcards, CASCADE DELETE)
                  ├── result  ENUM: remembered | repeat
                  ├── ease_factor     [snapshot after review]
                  ├── interval_days   [snapshot after review]
                  ├── next_review_at  [snapshot after review]
                  └── reviewed_at

languages
 ├── id (PK)
 ├── code (UNIQUE, BCP-47)
 ├── name
 └── flag
```

## Cardinalities

| Relationship | Cardinality |
|---|---|
| users → refresh_tokens | 1 : N |
| users → flashcard_sets | 1 : N |
| users → learning_sessions | 1 : N |
| flashcard_sets → flashcards | 1 : N |
| flashcard_sets → learning_sessions | 1 : N |
| learning_sessions → review_results | 1 : N |
| flashcards → review_results | 1 : N |
| languages → flashcard_sets | 1 : N |

## Key Indexes

| Table | Index | Purpose |
|---|---|---|
| users | `uq_users_email` | Unique constraint + login lookup |
| refresh_tokens | `uq_refresh_token_hash` | O(1) token validation |
| flashcards | `idx_cards_set_due (set_id, next_review_at)` | Core "due cards" query — must be O(log n) |
| learning_sessions | `idx_sessions_completed (user_id, completed_at)` | Streak and progress queries |
| review_results | `uq_review_session_card (session_id, card_id)` | Prevents duplicate reviews in a session |

## Design Notes

- **`card_count` is denormalized** on `flashcard_sets`. It avoids a `COUNT(*)` subquery on every
  deck list load. The `FlashcardSetsService` increments/decrements it on card create/delete/import.

- **Spaced repetition state lives on the card**, not in a separate table. This keeps the "due
  today" query simple: `WHERE set_id = ? AND next_review_at <= NOW()`. Historical SR snapshots
  are stored in `review_results` for analytics without polluting the hot path.

- **`review_results` stores post-review SR snapshots** (not the delta). This enables replay of
  the entire learning history for any card without recalculating the SM-2 chain.

- **No `user_id` on `flashcards`**. Ownership is established through `flashcard_sets.user_id`.
  All ownership checks join through the set. This keeps the cards table narrower and avoids a
  redundant FK.
