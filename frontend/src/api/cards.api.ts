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

export interface ImportFileResult {
  imported: number
  skipped: number
  setId: number
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

  importFile: async (file: File, setId?: number, setName?: string): Promise<ImportFileResult> => {
    const { useAuthStore } = await import('../store/auth.store')
    const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'
    const token = useAuthStore.getState().accessToken

    const formData = new FormData()
    formData.append('file', file)
    if (setId) formData.append('set_id', String(setId))
    if (setName) formData.append('set_name', setName)

    const res = await fetch(`${BASE_URL}/cards/import-file`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: 'include',
      body: formData,
    })
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || 'Import failed')
    }
    return res.json()
  },
}
