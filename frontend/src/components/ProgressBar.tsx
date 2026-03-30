interface ProgressBarProps {
  value: number
  max: number
  className?: string
}

export function ProgressBar({ value, max, className }: ProgressBarProps) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className={`w-full bg-gray-200 rounded-full h-2 ${className ?? ''}`}>
      <div
        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${percent}%` }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      />
    </div>
  )
}
