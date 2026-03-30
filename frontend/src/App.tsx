import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthInit } from './features/auth/useAuthInit'
import { ProtectedLayout } from './features/auth/ProtectedLayout'
import { LoginPage } from './features/auth/LoginPage'
import { RegisterPage } from './features/auth/RegisterPage'
import { SetListPage } from './features/cards/SetListPage'
import { AllCardsPage } from './features/cards/AllCardsPage'
import { SetDetailPage } from './features/cards/SetDetailPage'
import { SessionSetupPage } from './features/learning/SessionSetupPage'
import { SessionPlayPage } from './features/learning/SessionPlayPage'
import { SessionCompletePage } from './features/learning/SessionCompletePage'
import { StatsPage } from './features/stats/StatsPage'

export default function App() {
  useAuthInit()

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected routes */}
      <Route element={<ProtectedLayout />}>
        <Route index element={<Navigate to="/sets" replace />} />
        <Route path="/sets" element={<SetListPage />} />
        <Route path="/sets/:id" element={<SetDetailPage />} />
        <Route path="/cards" element={<AllCardsPage />} />
        <Route path="/learn/setup" element={<SessionSetupPage />} />
        <Route path="/learn/session/:id" element={<SessionPlayPage />} />
        <Route path="/learn/session/:id/done" element={<SessionCompletePage />} />
        <Route path="/stats" element={<StatsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/sets" replace />} />
    </Routes>
  )
}
