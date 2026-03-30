import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { setsApi } from '../../api/sets.api'
import { learningApi } from '../../api/learning.api'
import { useSessionStore } from '../../store/session.store'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'

export function SessionSetupPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const presetSetId = searchParams.get('setId') ? Number(searchParams.get('setId')) : undefined
  const setSession = useSessionStore((s) => s.actions.setSession)

  const [selectedSetId, setSelectedSetId] = useState<number | undefined>(presetSetId)
  const [cardCount, setCardCount] = useState(20)

  const { data: setsData } = useQuery({
    queryKey: ['sets'],
    queryFn: () => setsApi.getAll(),
  })

  const startMutation = useMutation({
    mutationFn: () =>
      learningApi.createSession({ setId: selectedSetId!, cardCount }),
    onSuccess: (data) => {
      setSession(data.sessionId, data.cards)
      navigate(`/learn/session/${data.sessionId}`)
    },
  })

  const sets = setsData?.data ?? []

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Start a session</h1>
      <p className="text-sm text-gray-500 mb-8">Choose a deck and how many cards to review</p>

      <div className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Deck</label>
          {sets.length === 0 ? (
            <p className="text-sm text-gray-500">No decks yet — create one first</p>
          ) : (
            <select
              value={selectedSetId ?? ''}
              onChange={(e) => setSelectedSetId(Number(e.target.value))}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select a deck...</option>
              {sets.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.language.flag} {s.name} ({s.cardCount} cards)
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Cards to study: <span className="text-primary-600 font-bold">{cardCount}</span>
          </label>
          <input
            type="range"
            min={1}
            max={100}
            value={cardCount}
            onChange={(e) => setCardCount(Number(e.target.value))}
            className="w-full accent-primary-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1</span>
            <span>100</span>
          </div>
        </div>

        <Button
          onClick={() => startMutation.mutate()}
          loading={startMutation.isPending}
          disabled={!selectedSetId}
          size="lg"
          className="w-full"
        >
          Start session
        </Button>
      </div>
    </div>
  )
}
