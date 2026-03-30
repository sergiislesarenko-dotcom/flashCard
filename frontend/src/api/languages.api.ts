import { apiClient } from './client'
import type { Language } from './types'

export const languagesApi = {
  getAll: () => apiClient<Language[]>('GET', '/languages'),
}
