import { apiClient } from './client'
import type { StatsOverview, DailyProgress } from './types'

export const statsApi = {
  getOverview: () =>
    apiClient<StatsOverview>('GET', '/stats/overview'),

  getProgress: (from: string, to: string) =>
    apiClient<{ data: DailyProgress[] }>('GET', `/stats/progress?from=${from}&to=${to}`),
}
