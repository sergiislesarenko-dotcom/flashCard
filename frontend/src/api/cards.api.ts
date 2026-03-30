import { apiClient } from './client'
import type { Flashcard, PaginatedResponse } from './types'

export interface CreateCardDto {
  setId: number
  front: string
  back: string
}

export interface UpdateCardDto {
  front?: string
  back?: string
}

export interface ImportCardsDto {
  setId: number
  cards: Array<{ front: string; back: string }>
}

export interface ImportResult {
  imported: number
  skipped: number
}

export const cardsApi = {
  getAll: (page = 1, pageSize = 25) =>
    apiClient<PaginatedResponse<Flashcard>>('GET', `/cards/all?page=${page}&pageSize=${pageSize}`),

  getBySet: (setId: number, page = 1, pageSize = 50) =>
    apiClient<PaginatedResponse<Flashcard>>('GET', `/cards?setId=${setId}&page=${page}&pageSize=${pageSize}`),

  create: (dto: CreateCardDto) =>
    apiClient<Flashcard>('POST', '/cards', dto),

  update: (id: number, dto: UpdateCardDto) =>
    apiClient<Flashcard>('PATCH', `/cards/${id}`, dto),

  delete: (id: number) =>
    apiClient('DELETE', `/cards/${id}`),

  import: (dto: ImportCardsDto) =>
    apiClient<ImportResult>('POST', '/cards/import', dto),
}
