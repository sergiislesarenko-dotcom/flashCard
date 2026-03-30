-- FlashLang Database Schema
-- MySQL 8.0+
-- This file is the authoritative source of truth for the database schema.
-- TypeORM synchronize is DISABLED. All schema changes go through this file.

CREATE DATABASE IF NOT EXISTS flashlang
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE flashlang;

-- ─────────────────────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE users (
  id            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  email         VARCHAR(255)     NOT NULL,
  display_name  VARCHAR(100)     NOT NULL,
  password_hash VARCHAR(255)     NOT NULL,  -- bcrypt, select: false in TypeORM
  created_at    TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- REFRESH TOKENS  (JWT refresh token rotation)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE refresh_tokens (
  id          BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
  user_id     BIGINT UNSIGNED  NOT NULL,
  token_hash  VARCHAR(255)     NOT NULL,  -- bcrypt hash of the raw token
  expires_at  TIMESTAMP        NOT NULL,
  created_at  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_refresh_token_hash (token_hash),
  KEY idx_refresh_user_id (user_id),

  CONSTRAINT fk_refresh_tokens_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- LANGUAGES
-- ─────────────────────────────────────────────────────────────
CREATE TABLE languages (
  id    TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code  VARCHAR(10)      NOT NULL,  -- BCP-47: 'en', 'zh-CN', etc.
  name  VARCHAR(100)     NOT NULL,
  flag  VARCHAR(10)      NULL,      -- emoji flag character

  PRIMARY KEY (id),
  UNIQUE KEY uq_languages_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- FLASHCARD SETS  (decks)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE flashcard_sets (
  id           BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT,
  user_id      BIGINT UNSIGNED   NOT NULL,
  language_id  TINYINT UNSIGNED  NOT NULL,
  name         VARCHAR(255)      NOT NULL,
  description  TEXT              NULL,
  card_count   INT UNSIGNED      NOT NULL DEFAULT 0,  -- denormalized; maintained by service layer
  created_at   TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_sets_user_id     (user_id),
  KEY idx_sets_language_id (language_id),

  CONSTRAINT fk_sets_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_sets_language
    FOREIGN KEY (language_id) REFERENCES languages (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- FLASHCARDS
-- Spaced repetition fields (SM-2 simplified):
--   ease_factor   starts at 2.50; increases on correct, decreases on wrong
--   interval_days days until next review
--   repetitions   consecutive correct answers
--   next_review_at date the card becomes due again
-- ─────────────────────────────────────────────────────────────
CREATE TABLE flashcards (
  id              BIGINT UNSIGNED   NOT NULL AUTO_INCREMENT,
  set_id          BIGINT UNSIGNED   NOT NULL,
  front           VARCHAR(500)      NOT NULL,  -- Russian word/phrase
  back            VARCHAR(500)      NOT NULL,  -- Translation in target language
  ease_factor     DECIMAL(4,2)      NOT NULL DEFAULT 2.50,
  interval_days   INT UNSIGNED      NOT NULL DEFAULT 1,
  repetitions     SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  next_review_at  TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  KEY idx_cards_set_id (set_id),

  -- Composite index critical for "due cards" query:
  -- WHERE set_id = ? AND next_review_at <= NOW() ORDER BY next_review_at ASC LIMIT ?
  KEY idx_cards_set_due (set_id, next_review_at),

  CONSTRAINT fk_cards_set
    FOREIGN KEY (set_id) REFERENCES flashcard_sets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- LEARNING SESSIONS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE learning_sessions (
  id                BIGINT UNSIGNED    NOT NULL AUTO_INCREMENT,
  user_id           BIGINT UNSIGNED    NOT NULL,
  set_id            BIGINT UNSIGNED    NOT NULL,
  status            ENUM('active','completed','abandoned') NOT NULL DEFAULT 'active',
  total_cards       SMALLINT UNSIGNED  NOT NULL DEFAULT 0,
  cards_reviewed    SMALLINT UNSIGNED  NOT NULL DEFAULT 0,
  cards_remembered  SMALLINT UNSIGNED  NOT NULL DEFAULT 0,
  started_at        TIMESTAMP          NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at      TIMESTAMP          NULL,

  PRIMARY KEY (id),
  KEY idx_sessions_user_id    (user_id),
  KEY idx_sessions_set_id     (set_id),
  KEY idx_sessions_completed  (user_id, completed_at),  -- used by streak query

  CONSTRAINT fk_sessions_user
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_sessions_set
    FOREIGN KEY (set_id) REFERENCES flashcard_sets (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────────────────────
-- REVIEW RESULTS  (one row per card per session)
-- Stores a snapshot of SR values AFTER each review for historical analysis.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE review_results (
  id              BIGINT UNSIGNED    NOT NULL AUTO_INCREMENT,
  session_id      BIGINT UNSIGNED    NOT NULL,
  card_id         BIGINT UNSIGNED    NOT NULL,
  result          ENUM('remembered','repeat') NOT NULL,
  ease_factor     DECIMAL(4,2)       NOT NULL,  -- value AFTER this review
  interval_days   INT UNSIGNED       NOT NULL,
  next_review_at  TIMESTAMP          NOT NULL,
  reviewed_at     TIMESTAMP          NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_review_session_card (session_id, card_id),  -- one review per card per session
  KEY idx_reviews_card_id (card_id),

  CONSTRAINT fk_reviews_session
    FOREIGN KEY (session_id) REFERENCES learning_sessions (id) ON DELETE CASCADE,
  CONSTRAINT fk_reviews_card
    FOREIGN KEY (card_id) REFERENCES flashcards (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
