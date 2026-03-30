import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { setsApi } from '../../api/sets.api'
import { cardsApi } from '../../api/cards.api'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'
import { CardEditorModal } from './CardEditorModal'
import type { Flashcard } from '../../api/types'

export function SetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const setId = Number(id)
  const [editCard, setEditCard] = useState<Flashcard | null>(null)
  const [showAddCard, setShowAddCard] = useState(false)
  const queryClient = useQueryClient()

  const { data: set, isLoading } = useQuery({
    queryKey: ['set', setId],
    queryFn: () => setsApi.getById(setId),
    enabled: !!setId,
  })

  const deleteMutation = useMutation({
    mutationFn: (cardId: number) => cardsApi.delete(cardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['set', setId] })
      queryClient.invalidateQueries({ queryKey: ['sets'] })
    },
  })

  if (isLoading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (!set) return <p className="text-red-600">Deck not found.</p>

  const cards = set.cards ?? []

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
        <Link to="/sets" className="hover:text-primary-600">My Decks</Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">{set.name}</span>
      </div>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{set.name}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {set.language.flag} {set.language.name} · {set.cardCount} cards
          </p>
          {set.description && <p className="text-sm text-gray-600 mt-1">{set.description}</p>}
        </div>
        <Link to={`/learn/setup?setId=${setId}`}>
          <Button>Study</Button>
        </Link>
      </div>

      <div className="flex gap-2 mb-4">
        <Button size="sm" variant="secondary" onClick={() => setShowAddCard(true)}>
          + Add card
        </Button>
      </div>

      {cards.length === 0 ? (
        <p className="text-gray-500 text-sm py-8 text-center">No cards yet. Add your first card!</p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Front</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Back</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Next review</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {cards.map((card) => (
                <tr key={card.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{card.front}</td>
                  <td className="px-4 py-3 text-gray-600">{card.back}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {card.nextReviewAt
                      ? new Date(card.nextReviewAt).toLocaleDateString()
                      : 'Today'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setEditCard(card)}
                        className="text-gray-400 hover:text-primary-600 text-xs"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => deleteMutation.mutate(card.id)}
                        className="text-gray-400 hover:text-red-500 text-xs"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAddCard && (
        <CardEditorModal setId={setId} onClose={() => setShowAddCard(false)} />
      )}
      {editCard && (
        <CardEditorModal setId={setId} card={editCard} onClose={() => setEditCard(null)} />
      )}
    </div>
  )
}
