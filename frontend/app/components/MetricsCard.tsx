interface MetricsCardProps {
  label: string
  value: string | number
  subtext?: string
  highlight?: boolean
  trend?: 'up' | 'down' | 'neutral'
}

export function MetricsCard({ 
  label, 
  value, 
  subtext, 
  highlight = false,
  trend = 'neutral' 
}: MetricsCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-800'
  }

  const trendIcons = {
    up: '▲',
    down: '▼',
    neutral: ''
  }

  return (
    <div className={`
      rounded-lg p-4 transition-all
      ${highlight 
        ? 'bg-turtle-50 border-2 border-turtle-300' 
        : 'bg-gray-50 border border-gray-200'
      }
    `}>
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${trendColors[trend]}`}>
        {trendIcons[trend]} {value}
      </div>
      {subtext && (
        <div className="text-xs text-gray-400 mt-1">{subtext}</div>
      )}
    </div>
  )
}
