import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { learningApi } from '../../api/learning.api'
import { useSessionStore } from '../../store/session.store'
import { Button } from '../../components/Button'

export function SessionCompletePage() {
  const { id } = useParams<{ id: string }>()
  const sessionId = Number(id)
  const sessionStore = useSessionStore()
  const navigate = useNavigate()

  const { data: session } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => learningApi.getSession(sessionId),
  })

  const remembered = session?.cardsRemembered ?? 0
  const reviewed = session?.cardsReviewed ?? 0
  const repeatCount = reviewed - remembered
  const accuracy = reviewed > 0 ? Math.round((remembered / reviewed) * 100) : 0
  const setId = session?.setId

  const handleStudyAgain = () => {
    sessionStore.actions.reset()
    if (setId) navigate(`/learn/setup?setId=${setId}`)
    else navigate('/learn/setup')
  }

  return (
    <div className="max-w-md mx-auto text-center">
      <div className="text-6xl mb-4">
        {accuracy >= 80 ? '🎉' : accuracy >= 60 ? '👍' : '💪'}
      </div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Session complete!</h1>
      <p className="text-gray-500 mb-8">Great work — keep reviewing daily for best results</p>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8">
        <div className="grid grid-cols-3 gap-4">
          <StatTile label="Reviewed" value={reviewed} />
          <StatTile label="Remembered" value={remembered} color="text-green-600" />
          <StatTile label="Repeat" value={repeatCount} color="text-orange-500" />
        </div>

        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Accuracy</span>
            <span className="font-semibold">{accuracy}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${accuracy >= 80 ? 'bg-green-500' : accuracy >= 60 ? 'bg-yellow-400' : 'bg-orange-400'}`}
              style={{ width: `${accuracy}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <Button size="lg" className="w-full" onClick={handleStudyAgain}>
          Study again
        </Button>
        <Link to="/sets">
          <Button variant="secondary" size="lg" className="w-full">
            Back to decks
          </Button>
        </Link>
        <Link to="/stats">
          <Button variant="ghost" size="sm" className="w-full text-gray-500">
            View progress stats →
          </Button>
        </Link>
      </div>
    </div>
  )
}

function StatTile({ label, value, color = 'text-gray-900' }: {
  label: string
  value: number
  color?: string
}) {
  return (
    <div className="text-center">
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  )
}
