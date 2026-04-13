'use client'

import { clsx } from 'clsx'

interface SignalBadgeProps {
  signal: 'BUY' | 'SELL' | 'HOLD'
  size?: 'sm' | 'md' | 'lg'
}

export function SignalBadge({ signal, size = 'lg' }: SignalBadgeProps) {
  const styles = {
    BUY: {
      bg: 'bg-green-100',
      border: 'border-green-500',
      text: 'text-green-800',
      icon: '📈'
    },
    SELL: {
      bg: 'bg-red-100',
      border: 'border-red-500',
      text: 'text-red-800',
      icon: '📉'
    },
    HOLD: {
      bg: 'bg-yellow-100',
      border: 'border-yellow-500',
      text: 'text-yellow-800',
      icon: '⏸️'
    }
  }[signal]

  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-lg'
  }

  return (
    <div
      className={clsx(
        'inline-flex items-center font-bold rounded-lg border-2',
        styles.bg,
        styles.border,
        styles.text,
        sizes[size]
      )}
    >
      <span className="mr-2">{styles.icon}</span>
      <span>{signal}</span>
      {signal !== 'HOLD' && (
        <span className={clsx(
          'ml-2 w-2 h-2 rounded-full',
          signal === 'BUY' ? 'bg-green-500' : 'bg-red-500',
          'animate-pulse'
        )} />
      )}
    </div>
  )
}
