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
  ReferenceArea,
  Scatter,
  Legend
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
  // 布林通道数据
  bb_upper?: number | null
  bb_middle?: number | null
  bb_lower?: number | null
  // 移动平均线
  sma_20?: number | null
  sma_10?: number | null
  // 信号标记
  signal?: 'BUY' | 'SELL' | 'HOLD'
}

interface StockChartProps {
  data: PriceData[]
  signal: 'BUY' | 'SELL' | 'HOLD'
}

export function StockChart({ data, signal }: StockChartProps) {
  const chartData = useMemo(() => {
    return data.map((item, index) => ({
      ...item,
      dateStr: new Date(item.date).toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric'
      }),
      // 买卖信号锚点
      buySignal: item.signal === 'BUY' ? item.close : null,
      sellSignal: item.signal === 'SELL' ? item.close : null,
      // 计算布林通道
      bb_upper: item.bb_upper || item.sma_20 ? (item.sma_20 || item.close) * 1.02 : null,
      bb_middle: item.sma_20 || item.close,
      bb_lower: item.bb_lower || item.sma_20 ? (item.sma_20 || item.close) * 0.98 : null,
    }))
  }, [data])

  const signalColor = {
    BUY: '#22c55e',
    SELL: '#ef4444',
    HOLD: '#f59e0b'
  }[signal]

  // 提取信号点
  const signalPoints = useMemo(() => {
    return chartData
      .filter(d => d.buySignal || d.sellSignal)
      .map(d => ({
        x: d.dateStr,
        y: d.buySignal || d.sellSignal || 0,
        type: d.buySignal ? 'BUY' : 'SELL'
      }))
  }, [chartData])

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
            tickFormatter={(value: number) => `$${value.toFixed(0)}`}
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
                high_20: '20日高点(入场)',
                low_10: '10日低点(出场)',
                sma_20: '20日均线',
                bb_upper: '布林上轨',
                bb_middle: '布林中轨',
                bb_lower: '布林下轨',
              }
              return [`$${value?.toFixed(2) || '-'}`, labels[name] || name]
            }}
          />

          <Legend />

          {/* 海龟通道区域 */}
          <ReferenceArea
            y1={chartData[0]?.low_10 || 0}
            y2={chartData[0]?.high_20 || 0}
            fill="#22c55e"
            fillOpacity={0.05}
          />

          {/* 20日通道上轨 - 入场阻力 */}
          <Line
            type="monotone"
            dataKey="high_20"
            stroke="#22c55e"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
            name="20日高点(入场)"
            connectNulls
          />

          {/* 10日通道下轨 - 出场支撑 */}
          <Line
            type="monotone"
            dataKey="low_10"
            stroke="#ef4444"
            strokeWidth={1.5}
            strokeDasharray="5 5"
            dot={false}
            name="10日低点(出场)"
            connectNulls
          />

          {/* 布林通道上轨 */}
          <Line
            type="monotone"
            dataKey="bb_upper"
            stroke="#8b5cf6"
            strokeWidth={1}
            strokeDasharray="3 3"
            dot={false}
            name="布林上轨"
            connectNulls
          />

          {/* 布林通道中轨 */}
          <Line
            type="monotone"
            dataKey="bb_middle"
            stroke="#8b5cf6"
            strokeWidth={1.5}
            dot={false}
            name="布林中轨"
            connectNulls
          />

          {/* 布林通道下轨 */}
          <Line
            type="monotone"
            dataKey="bb_lower"
            stroke="#8b5cf6"
            strokeWidth={1}
            strokeDasharray="3 3"
            dot={false}
            name="布林下轨"
            connectNulls
          />

          {/* 20日移动平均线 */}
          <Line
            type="monotone"
            dataKey="sma_20"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="20日均线"
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
            name="收盘价"
          />

          {/* 离散买卖信号锚点 - 符合PRD要求的信号叠加 */}
          <Scatter
            name="买入信号"
            data={chartData.filter(d => d.buySignal)}
            fill="#22c55e"
            symbol="triangleUp"
            dataKey="buySignal"
          />
          <Scatter
            name="卖出信号"
            data={chartData.filter(d => d.sellSignal)}
            fill="#ef4444"
            symbol="triangleDown"
            dataKey="sellSignal"
          />

          {/* 当前价格参考线 */}
          <ReferenceLine
            y={chartData[chartData.length - 1]?.close}
            stroke={signalColor}
            strokeDasharray="3 3"
            label={{
              value: `$${chartData[chartData.length - 1]?.close.toFixed(2)}`,
              position: 'right',
              fill: signalColor,
              fontSize: 12
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* 图例 */}
      <div className="flex flex-wrap justify-center items-center gap-4 mt-4 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-turtle-600 mr-2"></div>
          <span className="text-gray-600">收盘价</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-green-500 mr-2"></div>
          <span className="text-gray-600">20日高点(入场阻力)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-red-500 mr-2"></div>
          <span className="text-gray-600">10日低点(出场支撑)</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-purple-500 mr-2"></div>
          <span className="text-gray-600">布林通道</span>
        </div>
        <div className="flex items-center">
          <span className="text-green-500 mr-1">▲</span>
          <span className="text-gray-600">买入信号</span>
        </div>
        <div className="flex items-center">
          <span className="text-red-500 mr-1">▼</span>
          <span className="text-gray-600">卖出信号</span>
        </div>
      </div>
    </div>
  )
}
