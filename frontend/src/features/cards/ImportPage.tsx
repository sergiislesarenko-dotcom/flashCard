import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { cardsApi } from '../../api/cards.api'
import { setsApi } from '../../api/sets.api'
import { Button } from '../../components/Button'
import { Spinner } from '../../components/Spinner'

type Mode = 'existing' | 'new'

export function ImportPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [mode, setMode] = useState<Mode>('new')
  const [setId, setSetId] = useState<number | ''>('')
  const [setName, setSetName] = useState('')
  const [error, setError] = useState('')

  const { data: setsData, isLoading: setsLoading } = useQuery({
    queryKey: ['sets'],
    queryFn: () => setsApi.getAll(),
  })
  const sets = setsData?.data ?? []

  const importMutation = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('No file selected')
      return cardsApi.importFile(
        file,
        mode === 'existing' ? Number(setId) : undefined,
        mode === 'new' ? setName.trim() : undefined,
      )
    },
    onSuccess: (result) => {
      navigate(`/sets/${result.setId}`)
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (f) {
      setFile(f)
      setError('')
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const f = e.dataTransfer.files[0]
    if (f && (f.name.endsWith('.xls') || f.name.endsWith('.xlsx'))) {
      setFile(f)
      setError('')
    } else {
      setError('Only .xls and .xlsx files are supported')
    }
  }

  function handleSubmit() {
    setError('')
    if (!file) { setError('Select a file'); return }
    if (mode === 'existing' && !setId) { setError('Select a deck'); return }
    if (mode === 'new' && !setName.trim()) { setError('Enter a deck name'); return }
    importMutation.mutate()
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Import from Excel</h1>

      {/* File drop zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-gray-300 rounded-2xl p-8 text-center cursor-pointer hover:border-primary-400 transition-colors mb-6"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xls,.xlsx"
          onChange={handleFileChange}
          className="hidden"
        />
        {file ? (
          <div>
            <p className="text-sm font-medium text-gray-900">{file.name}</p>
            <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-500">Drag & drop .xls/.xlsx file here</p>
            <p className="text-xs text-gray-400 mt-1">or click to browse</p>
          </div>
        )}
      </div>

      {/* File format hint */}
      <div className="bg-gray-50 rounded-lg p-3 mb-6 text-xs text-gray-500">
        File must have columns: <strong>english</strong> and <strong>russian</strong>.
        Russian = front (word), English = back (translation).
      </div>

      {/* Mode selector */}
      <div className="flex gap-4 mb-4">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="radio"
            checked={mode === 'new'}
            onChange={() => setMode('new')}
            className="accent-primary-600"
          />
          Create new deck
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="radio"
            checked={mode === 'existing'}
            onChange={() => setMode('existing')}
            className="accent-primary-600"
          />
          Add to existing deck
        </label>
      </div>

      {/* Set selection */}
      {mode === 'new' ? (
        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 block mb-1">Deck name</label>
          <input
            value={setName}
            onChange={(e) => setSetName(e.target.value)}
            placeholder="e.g. Basic Vocabulary"
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      ) : (
        <div className="mb-6">
          <label className="text-sm font-medium text-gray-700 block mb-1">Select deck</label>
          {setsLoading ? (
            <Spinner size="sm" />
          ) : (
            <select
              value={setId}
              onChange={(e) => setSetId(e.target.value ? Number(e.target.value) : '')}
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
      )}

      {/* Error */}
      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {/* Actions */}
      <div className="flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={() => navigate(-1)}>
          Cancel
        </Button>
        <Button
          className="flex-1"
          onClick={handleSubmit}
          loading={importMutation.isPending}
          disabled={!file}
        >
          Import
        </Button>
      </div>
    </div>
  )
}
