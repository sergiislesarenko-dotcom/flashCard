import { apiClient } from './client'
import type { FlashcardSet, PaginatedResponse } from './types'

export interface CreateSetDto {
  name: string
  languageId: number
  description?: string
}

export interface UpdateSetDto {
  name?: string
  description?: string
}

export interface CreateSetFromCardsDto {
  name: string
  languageId: number
  description?: string
  cardIds: number[]
}

export const setsApi = {
  getAll: (page = 1, pageSize = 20) =>
    apiClient<PaginatedResponse<FlashcardSet>>('GET', `/sets?page=${page}&pageSize=${pageSize}`),

  getById: (id: number) =>
    apiClient<FlashcardSet & { cards: import('./types').Flashcard[] }>('GET', `/sets/${id}`),

  create: (dto: CreateSetDto) =>
    apiClient<FlashcardSet>('POST', '/sets', dto),

  createFromCards: (dto: CreateSetFromCardsDto) =>
    apiClient<FlashcardSet>('POST', '/sets/from-cards', dto),

  update: (id: number, dto: UpdateSetDto) =>
    apiClient<FlashcardSet>('PATCH', `/sets/${id}`, dto),

  delete: (id: number) =>
    apiClient('DELETE', `/sets/${id}`),
}
