import { useAuthStore } from '../store/auth.store'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export { ApiError }

export function isApiError(err: unknown, status?: number): err is ApiError {
  if (!(err instanceof ApiError)) return false
  if (status !== undefined) return err.status === status
  return true
}

let isRefreshing = false
let refreshPromise: Promise<string | null> | null = null

async function silentRefresh(): Promise<string | null> {
  if (isRefreshing && refreshPromise) return refreshPromise

  isRefreshing = true
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      })
      if (!res.ok) {
        useAuthStore.getState().clearAuth()
        return null
      }
      const data = (await res.json()) as { accessToken: string }
      useAuthStore.getState().setAccessToken(data.accessToken)
      return data.accessToken
    } catch {
      useAuthStore.getState().clearAuth()
      return null
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()

  return refreshPromise
}

const AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/logout']

export async function apiClient<T = void>(
  method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
  path: string,
  body?: unknown,
): Promise<T> {
  const accessToken = useAuthStore.getState().accessToken

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  // Silent token refresh on 401, but skip for auth endpoints
  if (response.status === 401 && !AUTH_PATHS.includes(path)) {
    const newToken = await silentRefresh()
    if (!newToken) {
      throw new ApiError(401, 'UNAUTHORIZED', 'Session expired')
    }

    // Retry original request with new token
    const retryResponse = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: { ...headers, Authorization: `Bearer ${newToken}` },
      credentials: 'include',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })

    if (!retryResponse.ok) {
      await throwApiError(retryResponse)
    }
    if (retryResponse.status === 204) return undefined as T
    return retryResponse.json() as Promise<T>
  }

  if (!response.ok) {
    await throwApiError(response)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function throwApiError(response: Response): Promise<never> {
  let code = 'INTERNAL_ERROR'
  let message = response.statusText

  try {
    const data = (await response.json()) as { error?: { code?: string; message?: string } }
    if (data.error?.code) code = data.error.code
    if (data.error?.message) message = data.error.message
  } catch {
    // Could not parse error body
  }

  throw new ApiError(response.status, code, message)
}
