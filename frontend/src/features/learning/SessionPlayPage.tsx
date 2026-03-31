import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { learningApi } from '../../api/learning.api'
import { cardsApi } from '../../api/cards.api'
import { useSessionStore } from '../../store/session.store'
import { FlashCard } from './components/FlashCard'
import { ProgressBar } from '../../components/ProgressBar'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'

export function SessionPlayPage() {
  const { id } = useParams<{ id: string }>()
  const sessionId = Number(id)
  const navigate = useNavigate()
  const [isFlipped, setIsFlipped] = useState(false)
  const [isCompleting, setIsCompleting] = useState(false)
  const [showExamples, setShowExamples] = useState(false)

  const { cards, currentIndex, actions } = useSessionStore((s) => ({
    cards: s.cards,
    currentIndex: s.currentIndex,
    actions: s.actions,
  }))

  function handleSkip() {
    const nextIndex = currentIndex + 1
    if (nextIndex >= cards.length) {
      setIsCompleting(true)
      learningApi
        .completeSession(sessionId)
        .then(() => navigate(`/learn/session/${sessionId}/done`))
        .catch(() => navigate(`/learn/session/${sessionId}/done`))
    } else {
      actions.advance()
      setIsFlipped(false)
      setShowExamples(false)
    }
  }

  const reviewMutation = useMutation({
    mutationFn: (result: 'remembered' | 'repeat') =>
      learningApi.submitReview(sessionId, {
        cardId: cards[currentIndex].id,
        result,
      }),
    onSuccess: (_, result) => {
      actions.recordResult(cards[currentIndex].id, result)
      const nextIndex = currentIndex + 1
      if (nextIndex >= cards.length) {
        // All cards reviewed — complete the session
        setIsCompleting(true)
        learningApi
          .completeSession(sessionId)
          .then(() => navigate(`/learn/session/${sessionId}/done`))
          .catch(() => navigate(`/learn/session/${sessionId}/done`))
      } else {
        actions.advance()
        setIsFlipped(false)
        setShowExamples(false)
      }
    },
  })

  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isFlipped) {
        if (e.code === 'Space') { e.preventDefault(); setIsFlipped(true) }
        return
      }
      if (e.key === '1') reviewMutation.mutate('remembered')
      if (e.key === '2') reviewMutation.mutate('repeat')
    },
    [isFlipped, reviewMutation],
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  if (!cards.length || isCompleting) {
    return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  }

  const currentCard = cards[currentIndex]

  const examplesQuery = useQuery({
    queryKey: ['card-examples', currentCard?.id],
    queryFn: () => cardsApi.getExamples(currentCard!.id),
    enabled: showExamples && !!currentCard,
  })

  if (!currentCard) {
    return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  }

  const progress = currentIndex
  const total = cards.length

  return (
    <div className="max-w-lg mx-auto">
      {/* Progress */}
      <div className="flex items-center justify-between mb-3 text-sm text-gray-500">
        <span>{currentIndex + 1} / {total}</span>
        <span className="text-xs">Space to flip · 1 = remembered · 2 = repeat</span>
      </div>
      <ProgressBar value={progress} max={total} className="mb-8" />

      {/* Card */}
      <div className="flex justify-center mb-8">
        <FlashCard
          front={currentCard.front}
          back={currentCard.back}
          isFlipped={isFlipped}
          onFlip={() => setIsFlipped((f) => !f)}
        />
      </div>

      {/* Examples toggle */}
      <div className="flex justify-center mb-4">
        <button
          onClick={() => setShowExamples((v) => !v)}
          className="text-sm text-primary-600 hover:text-primary-700 underline"
        >
          {showExamples ? 'Hide examples' : 'Examples'}
        </button>
      </div>

      {showExamples && (
        <div className="bg-gray-50 rounded-xl p-4 mb-6 text-sm">
          {examplesQuery.isLoading && <p className="text-gray-400">Loading...</p>}
          {examplesQuery.data && examplesQuery.data.length === 0 && (
            <p className="text-gray-400">No examples for this card</p>
          )}
          {examplesQuery.data && examplesQuery.data.length > 0 && (
            <ul className="space-y-2">
              {examplesQuery.data.map((ex) => (
                <li key={ex.id} className="text-gray-700">{ex.text}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Actions — only visible after flip */}
      {isFlipped ? (
        <div className="flex gap-4">
          <Button
            variant="secondary"
            size="lg"
            className="flex-1 border-orange-300 text-orange-700 hover:bg-orange-50"
            onClick={() => reviewMutation.mutate('repeat')}
            loading={reviewMutation.isPending}
          >
            Repeat later
          </Button>
          <Button
            size="lg"
            className="flex-1 bg-green-600 hover:bg-green-700"
            onClick={() => reviewMutation.mutate('remembered')}
            loading={reviewMutation.isPending}
          >
            I remembered ✓
          </Button>
        </div>
      ) : (
        <div className="flex gap-3">
          <Button
            size="lg"
            variant="secondary"
            className="flex-1"
            disabled={currentIndex === 0}
            onClick={() => { actions.goBack(); setIsFlipped(false); setShowExamples(false) }}
          >
            ← Back
          </Button>
          <Button
            size="lg"
            variant="secondary"
            className="flex-1"
            onClick={() => setIsFlipped(true)}
          >
            Reveal translation
          </Button>
          <Button
            size="lg"
            variant="secondary"
            className="flex-1"
            onClick={handleSkip}
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  )
}
