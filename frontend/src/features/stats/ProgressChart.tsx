import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { statsApi } from '../../api/stats.api'
import { Spinner } from '../../components/Spinner'

interface Props {
  from: string
  to: string
}

export function ProgressChart({ from, to }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['stats', 'progress', from, to],
    queryFn: () => statsApi.getProgress(from, to),
    staleTime: 2 * 60 * 1000,
  })

  if (isLoading) return <div className="flex justify-center py-8"><Spinner /></div>

  const chartData = (data?.data ?? []).map((d) => ({
    date: new Date(d.date).toLocaleDateString('en', { month: 'short', day: 'numeric' }),
    Reviewed: d.cardsReviewed,
    Remembered: d.cardsRemembered,
  }))

  if (chartData.length === 0) {
    return (
      <p className="text-center text-gray-400 py-8 text-sm">
        No activity in this period yet. Start a session!
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="Reviewed" fill="#c7d2fe" radius={[4, 4, 0, 0]} />
        <Bar dataKey="Remembered" fill="#4f46e5" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
