import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth.store'
import { authApi } from '../../api/auth.api'

export function NavBar() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await authApi.logout().catch(() => {})
    clearAuth()
    navigate('/login')
  }

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/sets" className="text-lg font-bold text-primary-600">
            FlashLang
          </Link>
          <Link to="/sets" className="text-sm text-gray-600 hover:text-gray-900">
            My Decks
          </Link>
          <Link to="/stats" className="text-sm text-gray-600 hover:text-gray-900">
            Stats
          </Link>
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <span className="text-sm text-gray-500">{user.displayName}</span>
          )}
          <button
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}
