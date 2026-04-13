'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

interface Position {
  id: number
  ticker: string
  position_type: string
  units: number
  shares: number | null
  avg_entry_price: number | null
  n_value_at_entry: number | null
  stop_loss_price: number | null
  opened_at: string
  is_closed: boolean
}

interface PortfolioSummary {
  total_positions: number
  total_exposure: number
  long_units: number
  short_units: number
  net_exposure: number
  limits: {
    single_market: number
    high_correlation: number
    low_correlation: number
    single_direction: number
  }
  utilization: {
    long: number
    short: number
  }
}

export default function PositionsPage() {
  const [positions, setPositions] = useState<Position[]>([])
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [showClosed, setShowClosed] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [positionsRes, summaryRes] = await Promise.all([
        axios.get(`/api/v1/positions?include_closed=${showClosed}`),
        axios.get('/api/v1/positions/summary')
      ])
      setPositions(positionsRes.data)
      setSummary(summaryRes.data)
    } catch (err) {
      console.error('获取数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [showClosed])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">💼 持仓管理</h1>

      {/* 投资组合摘要 */}
      {summary && (
        <div className="grid md:grid-cols-4 gap-4 mb-6">
          <SummaryCard
            label="总持仓数"
            value={summary.total_positions.toString()}
            icon="📊"
          />
          <SummaryCard
            label="多头单位"
            value={summary.long_units.toString()}
            icon="📈"
            color="text-green-600"
          />
          <SummaryCard
            label="空头单位"
            value={summary.short_units.toString()}
            icon="📉"
            color="text-red-600"
          />
          <SummaryCard
            label="净敞口"
            value={summary.net_exposure.toString()}
            icon="⚖️"
          />
        </div>
      )}

      {/* 风险限制 */}
      {summary && (
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">🛡️ 风险限制</h2>
          <div className="grid md:grid-cols-4 gap-4">
            <LimitCard
              label="单一市场"
              current={summary.long_units + summary.short_units}
              max={summary.limits.single_market}
              description="单个标的最多4单位"
            />
            <LimitCard
              label="高关联市场"
              current={summary.long_units}
              max={summary.limits.high_correlation}
              description="高关联品种最多6单位"
            />
            <LimitCard
              label="弱关联市场"
              current={summary.short_units}
              max={summary.limits.low_correlation}
              description="弱关联品种最多10单位"
            />
            <LimitCard
              label="单向总敞口"
              current={summary.long_units}
              max={summary.limits.single_direction}
              description="单方向最多12单位"
            />
          </div>
        </div>
      )}

      {/* 持仓列表 */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-800">持仓列表</h2>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showClosed}
              onChange={(e) => setShowClosed(e.target.checked)}
              className="w-4 h-4 text-turtle-600 rounded"
            />
            <span className="text-sm text-gray-600">显示已平仓</span>
          </label>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-500">加载中...</div>
        ) : positions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">暂无持仓记录</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">标的</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">类型</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">单位</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">股数</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">入场价</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">止损价</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">开仓时间</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">状态</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {positions.map((position) => (
                  <tr key={position.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold text-gray-800">
                      {position.ticker}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${
                        position.position_type === 'LONG' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {position.position_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {position.units}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {position.shares?.toFixed(0) || '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {position.avg_entry_price ? `$${position.avg_entry_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {position.stop_loss_price ? `$${position.stop_loss_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">
                      {formatDate(position.opened_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded ${
                        position.is_closed 
                          ? 'bg-gray-100 text-gray-600' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {position.is_closed ? '已平仓' : '持仓中'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function SummaryCard({ label, value, icon, color = 'text-gray-800' }: { label: string; value: string; icon: string; color?: string }) {
  return (
    <div className="bg-white rounded-xl shadow-md p-4">
      <div className="flex items-center space-x-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-sm text-gray-500">{label}</div>
          <div className={`text-2xl font-bold ${color}`}>{value}</div>
        </div>
      </div>
    </div>
  )
}

function LimitCard({ label, current, max, description }: { label: string; current: number; max: number; description: string }) {
  const percentage = Math.min((current / max) * 100, 100)
  const color = percentage >= 80 ? 'bg-red-500' : percentage >= 60 ? 'bg-yellow-500' : 'bg-turtle-500'
  
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="text-sm text-gray-600 mb-2">{label}</div>
      <div className="flex items-end space-x-2 mb-2">
        <span className="text-xl font-bold text-gray-800">{current}</span>
        <span className="text-gray-400">/ {max}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className={`h-2 rounded-full transition-all ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="text-xs text-gray-400 mt-1">{description}</div>
    </div>
  )
}
