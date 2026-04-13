'use client'

import { useMemo } from 'react'
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts'

interface PriceData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  high_20: number | null
  low_10: number | null
}

interface StockChartProps {
  data: PriceData[]
  signal: 'BUY' | 'SELL' | 'HOLD'
}

export function StockChart({ data, signal }: StockChartProps) {
  const chartData = useMemo(() => {
    return data.map(item => ({
      ...item,
      dateStr: new Date(item.date).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric'
      })
    }))
  }, [data])

  const signalColor = {
    BUY: '#22c55e',
    SELL: '#ef4444',
    HOLD: '#f59e0b'
  }[signal]

  if (!data || data.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center text-gray-400">
        暂无数据
      </div>
    )
  }

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          <XAxis
            dataKey="dateStr"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
            formatter={(value: number, name: string) => {
              const labels: Record<string, string> = {
                close: '收盘价',
                high_20: '20日高点',
                low_10: '10日低点'
              }
              return [`$${value.toFixed(2)}`, labels[name] || name]
            }}
          />

          {/* 通道区域 */}
          <ReferenceArea
            y1={chartData[0]?.low_10 || 0}
            y2={chartData[0]?.high_20 || 0}
            fill="#22c55e"
            fillOpacity={0.05}
          />

          {/* 20日通道上轨 */}
          <Line
            type="monotone"
            dataKey="high_20"
            stroke="#22c55e"
            strokeWidth={1.5}
            dot={false}
            name="high_20"
            connectNulls
          />

          {/* 10日通道下轨 */}
          <Line
            type="monotone"
            dataKey="low_10"
            stroke="#ef4444"
            strokeWidth={1.5}
            dot={false}
            name="low_10"
            connectNulls
          />

          {/* 价格线 */}
          <Area
            type="monotone"
            dataKey="close"
            stroke={signalColor}
            strokeWidth={2}
            fill={signalColor}
            fillOpacity={0.1}
            name="close"
          />

          {/* 当前价格参考线 */}
          <ReferenceLine
            y={chartData[chartData.length - 1]?.close}
            stroke={signalColor}
            strokeDasharray="3 3"
            label={{
              value: `当前: $${chartData[chartData.length - 1]?.close.toFixed(2)}`,
              position: 'right',
              fill: signalColor,
              fontSize: 12
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* 图例 */}
      <div className="flex justify-center items-center space-x-6 mt-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-turtle-600 mr-2"></div>
          <span className="text-gray-600">收盘价</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-green-500 mr-2"></div>
          <span className="text-gray-600">20日高点 (入场阻力)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-red-500 mr-2"></div>
          <span className="text-gray-600">10日低点 (出场支撑)</span>
        </div>
      </div>
    </div>
  )
}
