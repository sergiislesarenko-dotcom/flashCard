import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { setsApi } from '../../api/sets.api'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'
import { SetEditorModal } from './SetEditorModal'
import type { FlashcardSet } from '../../api/types'

export function SetListPage() {
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['sets'],
    queryFn: () => setsApi.getAll(),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => setsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sets'] }),
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) => setsApi.update(id, { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sets'] }),
  })

  if (isLoading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (error) return <p className="text-red-600">Failed to load decks.</p>

  const sets = data?.data ?? []

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Decks</h1>
        <Button onClick={() => setShowCreate(true)}>+ New Deck</Button>
      </div>

      {sets.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-4">No decks yet</p>
          <Button onClick={() => setShowCreate(true)}>Create your first deck</Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sets.map((set) => (
            <SetCard
              key={set.id}
              set={set}
              onDelete={() => deleteMutation.mutate(set.id)}
              onRename={(name) => renameMutation.mutate({ id: set.id, name })}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <SetEditorModal onClose={() => setShowCreate(false)} />
      )}
    </div>
  )
}

function SetCard({ set, onDelete, onRename }: { set: FlashcardSet; onDelete: () => void; onRename: (name: string) => void }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState(set.name)

  function handleSave() {
    const trimmed = editName.trim()
    if (trimmed && trimmed !== set.name) {
      onRename(trimmed)
    }
    setIsEditing(false)
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <span className="text-2xl mr-2">{set.language.flag}</span>
          <span className="text-xs font-medium text-gray-400 uppercase">{set.language.name}</span>
        </div>
        <button
          onClick={(e) => { e.preventDefault(); onDelete() }}
          className="text-gray-300 hover:text-red-400 transition-colors text-sm"
        >
          ✕
        </button>
      </div>

      {isEditing ? (
        <div className="flex items-center gap-2 mb-2">
          <input
            autoFocus
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSave(); if (e.key === 'Escape') setIsEditing(false) }}
            className="flex-1 min-w-0 px-2 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button onClick={handleSave} className="text-green-600 hover:text-green-700 text-sm font-medium">Save</button>
          <button onClick={() => { setEditName(set.name); setIsEditing(false) }} className="text-gray-400 hover:text-gray-600 text-sm">Cancel</button>
        </div>
      ) : (
        <div className="flex items-center gap-2 mb-2">
          <Link to={`/sets/${set.id}`} className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 hover:text-primary-600 transition-colors truncate">
              {set.name}
            </h3>
          </Link>
          <button
            onClick={() => setIsEditing(true)}
            className="text-gray-300 hover:text-primary-500 transition-colors text-sm shrink-0"
            title="Edit name"
          >
            Edit
          </button>
        </div>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{set.cardCount} cards</span>
        {(set.dueCount ?? 0) > 0 && (
          <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
            {set.dueCount} due
          </span>
        )}
      </div>

      <Link to={`/learn/setup?setId=${set.id}`}>
        <Button size="sm" className="w-full mt-4">Study now</Button>
      </Link>
    </div>
  )
}
