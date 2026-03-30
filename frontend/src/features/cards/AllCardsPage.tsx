import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { cardsApi } from '../../api/cards.api'
import { setsApi } from '../../api/sets.api'
import { languagesApi } from '../../api/languages.api'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'
import type { Flashcard } from '../../api/types'

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100]

export function AllCardsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [setName, setSetName] = useState('')
  const [languageId, setLanguageId] = useState<number | ''>('')
  const [error, setError] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['cards', 'all', page, pageSize],
    queryFn: () => cardsApi.getAll(page, pageSize),
  })

  const { data: languages = [] } = useQuery({
    queryKey: ['languages'],
    queryFn: languagesApi.getAll,
    staleTime: Infinity,
  })

  const createMutation = useMutation({
    mutationFn: setsApi.createFromCards,
    onSuccess: (newSet) => {
      queryClient.invalidateQueries({ queryKey: ['sets'] })
      navigate(`/sets/${newSet.id}`)
    },
  })

  const cards: Flashcard[] = data?.data ?? []
  const pagination = data?.pagination
  const totalPages = pagination ? Math.ceil(pagination.total / pagination.pageSize) : 0

  function toggleCard(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleAll() {
    if (cards.every((c) => selected.has(c.id))) {
      setSelected((prev) => {
        const next = new Set(prev)
        cards.forEach((c) => next.delete(c.id))
        return next
      })
    } else {
      setSelected((prev) => {
        const next = new Set(prev)
        cards.forEach((c) => next.add(c.id))
        return next
      })
    }
  }

  function handleSave() {
    setError('')
    if (!setName.trim()) { setError('Enter a set name'); return }
    if (!languageId) { setError('Select a language'); return }
    if (selected.size === 0) { setError('Select at least one card'); return }

    createMutation.mutate({
      name: setName.trim(),
      languageId: Number(languageId),
      cardIds: Array.from(selected),
    })
  }

  function handleCancel() {
    setSelected(new Set())
    setSetName('')
    setLanguageId('')
    setError('')
  }

  if (isLoading) {
    return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  }

  const allOnPageSelected = cards.length > 0 && cards.every((c) => selected.has(c.id))

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">All Cards</h1>

      {/* Set creation form */}
      <div className="bg-white rounded-2xl border border-gray-200 p-4 mb-6">
        <p className="text-sm font-medium text-gray-700 mb-3">
          Create a new deck from selected cards ({selected.size} selected)
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1 flex-1 min-w-[180px]">
            <label className="text-xs text-gray-500">Deck name</label>
            <input
              value={setName}
              onChange={(e) => setSetName(e.target.value)}
              placeholder="e.g. Basic Greetings"
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div className="flex flex-col gap-1 min-w-[160px]">
            <label className="text-xs text-gray-500">Language</label>
            <select
              value={languageId}
              onChange={(e) => setLanguageId(e.target.value ? Number(e.target.value) : '')}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select...</option>
              {languages.map((l) => (
                <option key={l.id} value={l.id}>{l.flag} {l.name}</option>
              ))}
            </select>
          </div>
          <Button onClick={handleSave} loading={createMutation.isPending} disabled={selected.size === 0}>
            Save
          </Button>
          <Button variant="secondary" onClick={handleCancel}>
            Cancel
          </Button>
        </div>
        {(error || createMutation.error) && (
          <p className="text-xs text-red-600 mt-2">{error || 'Failed to create deck'}</p>
        )}
      </div>

      {/* Cards table */}
      <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="w-10 px-3 py-3">
                <input
                  type="checkbox"
                  checked={allOnPageSelected}
                  onChange={toggleAll}
                  className="rounded border-gray-300"
                />
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Front</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Back</th>
            </tr>
          </thead>
          <tbody>
            {cards.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-400">
                  No cards found
                </td>
              </tr>
            ) : (
              cards.map((card) => (
                <tr
                  key={card.id}
                  className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => toggleCard(card.id)}
                >
                  <td className="px-3 py-3 text-center">
                    <input
                      type="checkbox"
                      checked={selected.has(card.id)}
                      onChange={() => toggleCard(card.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded border-gray-300"
                    />
                  </td>
                  <td className="px-4 py-3 text-gray-900">{card.front}</td>
                  <td className="px-4 py-3 text-gray-700">{card.back}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1) }}
              className="rounded border border-gray-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {PAGE_SIZE_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
            <span className="ml-2">
              {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, pagination.total)} of {pagination.total}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Prev
            </Button>
            <span className="px-2">{page} / {totalPages}</span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
