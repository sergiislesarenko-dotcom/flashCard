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

export const setsApi = {
  getAll: (page = 1, pageSize = 20) =>
    apiClient<PaginatedResponse<FlashcardSet>>('GET', `/sets?page=${page}&pageSize=${pageSize}`),

  getById: (id: number) =>
    apiClient<FlashcardSet & { cards: import('./types').Flashcard[] }>('GET', `/sets/${id}`),

  create: (dto: CreateSetDto) =>
    apiClient<FlashcardSet>('POST', '/sets', dto),

  update: (id: number, dto: UpdateSetDto) =>
    apiClient<FlashcardSet>('PATCH', `/sets/${id}`, dto),

  delete: (id: number) =>
    apiClient('DELETE', `/sets/${id}`),
}
