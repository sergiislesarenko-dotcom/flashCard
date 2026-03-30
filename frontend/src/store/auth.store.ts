import { create } from 'zustand'
import type { User } from '../api/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isInitializing: boolean  // true until the first silent refresh attempt completes
  setAuth: (user: User, accessToken: string) => void
  setAccessToken: (token: string) => void
  setInitialized: () => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  accessToken: null,
  isAuthenticated: false,
  isInitializing: true,

  setAuth: (user, accessToken) =>
    set({ user, accessToken, isAuthenticated: true, isInitializing: false }),

  setAccessToken: (accessToken) =>
    set({ accessToken }),

  setInitialized: () =>
    set({ isInitializing: false }),

  clearAuth: () =>
    set({ user: null, accessToken: null, isAuthenticated: false, isInitializing: false }),
}))
