// Shared TypeScript interfaces mirroring API response shapes.
// These are the single source of truth for frontend type safety.

export interface User {
  id: number
  email: string
  displayName: string
  createdAt: string
}

export interface Language {
  id: number
  code: string
  name: string
  flag: string
}

export interface FlashcardSet {
  id: number
  name: string
  description?: string
  language: Language
  cardCount: number
  dueCount?: number
  createdAt: string
}

export interface Flashcard {
  id: number
  setId: number
  front: string
  back: string
  easeFactor: number
  intervalDays: number
  repetitions: number
  nextReviewAt: string | null
}

export interface CardExample {
  id: number
  cardId: number
  text: string
}

export interface SessionCard {
  id: number
  front: string
  back: string
}

export interface LearningSession {
  sessionId: number
  setId: number
  status: 'active' | 'completed' | 'abandoned'
  totalCards: number
  cardsReviewed: number
  cardsRemembered: number
  startedAt: string
  completedAt: string | null
}

export interface SessionStartResponse {
  sessionId: number
  setId: number
  cards: SessionCard[]
  totalCards: number
  startedAt: string
}

export interface ReviewResult {
  cardId: number
  result: 'remembered' | 'repeat'
  nextReviewAt: string
  intervalDays: number
  easeFactor: number
  repetitions: number
}

export interface SessionSummary {
  sessionId: number
  status: string
  totalCards: number
  cardsReviewed: number
  cardsRemembered: number
  repeatCount: number
  accuracyPercent: number
  completedAt: string
}

export interface StatsOverview {
  totalSets: number
  totalCards: number
  dueToday: number
  sessionsCompleted: number
  streakDays: number
  averageAccuracy: number
}

export interface DailyProgress {
  date: string
  sessionsCompleted: number
  cardsReviewed: number
  cardsRemembered: number
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    pageSize: number
    total: number
  }
}

export interface ApiErrorResponse {
  error: {
    code: string
    message: string
    details?: Array<{ field: string; issue: string }>
  }
}
