import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { statsApi } from '../../api/stats.api'
import { Spinner } from '../../components/Spinner'
import { ProgressChart } from './ProgressChart'

export function StatsPage() {
  const [range, setRange] = useState<7 | 30>(30)

  const { data: overview, isLoading } = useQuery({
    queryKey: ['stats', 'overview'],
    queryFn: statsApi.getOverview,
    staleTime: 2 * 60 * 1000,
  })

  const to = new Date().toISOString().slice(0, 10)
  const from = (() => {
    const d = new Date()
    d.setDate(d.getDate() - range + 1)
    return d.toISOString().slice(0, 10)
  })()

  if (isLoading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Learning Progress</h1>

      {/* Overview tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
        <StatTile label="Total cards" value={overview?.totalCards ?? 0} />
        <StatTile
          label="Due today"
          value={overview?.dueToday ?? 0}
          highlight={(overview?.dueToday ?? 0) > 0}
        />
        <StatTile label="Sessions done" value={overview?.sessionsCompleted ?? 0} />
        <StatTile
          label="Day streak"
          value={overview?.streakDays ?? 0}
          suffix={overview?.streakDays === 1 ? 'day' : 'days'}
          icon="🔥"
        />
        <StatTile label="Avg accuracy" value={overview?.averageAccuracy ?? 0} suffix="%" />
        <StatTile label="Decks" value={overview?.totalSets ?? 0} />
      </div>

      {/* Progress chart */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Daily activity</h2>
          <div className="flex gap-2">
            {([7, 30] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3 py-1 rounded-lg text-sm ${
                  range === r
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {r}d
              </button>
            ))}
          </div>
        </div>
        <ProgressChart from={from} to={to} />
      </div>
    </div>
  )
}

function StatTile({
  label,
  value,
  suffix,
  icon,
  highlight,
}: {
  label: string
  value: number
  suffix?: string
  icon?: string
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        highlight ? 'bg-orange-50 border-orange-200' : 'bg-white border-gray-200'
      }`}
    >
      <p className={`text-3xl font-bold ${highlight ? 'text-orange-600' : 'text-gray-900'}`}>
        {icon && <span className="mr-1">{icon}</span>}
        {value}
        {suffix && <span className="text-xl ml-1">{suffix}</span>}
      </p>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  )
}
