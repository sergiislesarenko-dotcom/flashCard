import { create } from 'zustand'
import type { SessionCard } from '../api/types'

interface SessionState {
  sessionId: number | null
  languageCode: string
  cards: SessionCard[]
  currentIndex: number
  results: Record<number, 'remembered' | 'repeat'>
  actions: {
    setSession: (id: number, cards: SessionCard[], languageCode: string) => void
    recordResult: (cardId: number, result: 'remembered' | 'repeat') => void
    advance: () => void
    goBack: () => void
    reset: () => void
  }
}

export const useSessionStore = create<SessionState>()((set) => ({
  sessionId: null,
  languageCode: 'en',
  cards: [],
  currentIndex: 0,
  results: {},

  actions: {
    setSession: (id, cards, languageCode) =>
      set({ sessionId: id, cards, currentIndex: 0, results: {}, languageCode }),

    recordResult: (cardId, result) =>
      set((s) => ({ results: { ...s.results, [cardId]: result } })),

    advance: () =>
      set((s) => ({ currentIndex: s.currentIndex + 1 })),

    goBack: () =>
      set((s) => ({ currentIndex: Math.max(0, s.currentIndex - 1) })),

    reset: () =>
      set({ sessionId: null, cards: [], currentIndex: 0, results: {} }),
  },
}))
