import { useEffect } from 'react'
import { authApi } from '../../api/auth.api'
import { useAuthStore } from '../../store/auth.store'
import type { User } from '../../api/types'

/** Decode a JWT payload without a library. */
function parseJwt(token: string): { sub: number; email: string } | null {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload)) as { sub: number; email: string }
  } catch {
    return null
  }
}

/**
 * Called once on app mount. Silently calls POST /auth/refresh using the
 * HttpOnly refresh_token cookie. On success, reconstructs the user from
 * the JWT payload and marks the session as authenticated.
 * On failure, marks isInitializing=false so ProtectedLayout can redirect.
 */
export function useAuthInit() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const { setAuth, setInitialized } = useAuthStore.getState()

  useEffect(() => {
    if (isAuthenticated) {
      setInitialized()
      return
    }
    authApi
      .refresh()
      .then((res) => {
        const payload = parseJwt(res.accessToken)
        if (payload) {
          const user: User = {
            id: payload.sub,
            email: payload.email,
            displayName: payload.email, // best we can do without a /me endpoint
            createdAt: '',
          }
          setAuth(user, res.accessToken)
        } else {
          setInitialized()
        }
      })
      .catch(() => {
        // Cookie expired or absent — mark init done so redirect fires
        setInitialized()
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
}
