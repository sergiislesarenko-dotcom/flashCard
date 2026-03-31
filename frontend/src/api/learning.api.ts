import { apiClient } from './client'
import type {
  SessionStartResponse,
  LearningSession,
  ReviewResult,
  SessionSummary,
} from './types'

export interface CreateSessionDto {
  setId: number
  cardCount?: number
}

export interface SubmitReviewDto {
  cardId: number
  result: 'remembered' | 'repeat'
}

export const learningApi = {
  createSession: (dto: CreateSessionDto) =>
    apiClient<SessionStartResponse>('POST', '/learning/sessions', dto),

  getSession: (sessionId: number) =>
    apiClient<LearningSession>('GET', `/learning/sessions/${sessionId}`),

  submitReview: (sessionId: number, dto: SubmitReviewDto) =>
    apiClient<ReviewResult>('POST', `/learning/sessions/${sessionId}/reviews`, dto),

  completeSession: (sessionId: number) =>
    apiClient<SessionSummary>('POST', `/learning/sessions/${sessionId}/complete`),
}
