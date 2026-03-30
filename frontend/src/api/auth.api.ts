import { apiClient } from './client'
import type { User } from './types'

export interface RegisterDto {
  email: string
  password: string
  displayName: string
}

export interface LoginDto {
  email: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  expiresIn: number
  user: User
}

export interface RefreshResponse {
  accessToken: string
  expiresIn: number
}

export const authApi = {
  register: (dto: RegisterDto) =>
    apiClient<User>('POST', '/auth/register', dto),

  login: (dto: LoginDto) =>
    apiClient<LoginResponse>('POST', '/auth/login', dto),

  refresh: () =>
    apiClient<RefreshResponse>('POST', '/auth/refresh'),

  logout: () =>
    apiClient('POST', '/auth/logout'),
}
