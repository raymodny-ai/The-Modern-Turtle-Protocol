'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'

interface HistoryRecord {
  id: number
  ticker: string
  analysis_time: string
  current_price: number
  signal: 'BUY' | 'SELL' | 'HOLD'
  signal_reason: string | null
  high_20_day: number | null
  low_10_day: number | null
  n_value: number | null
  recommended_units: number | null
  position_size: number | null
  account_equity: number
  is_active: boolean
}

interface HistoryResponse {
  success: boolean
  total: number
  limit: number
  offset: number
  records: HistoryRecord[]
}

export default function HistoryPage() {
  const [records, setRecords] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({ total: 0, limit: 20, offset: 0 })
  const [filter, setFilter] = useState<{ ticker?: string; signal?: string }>({})

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: pagination.limit.toString(),
        offset: pagination.offset.toString()
      })
      if (filter.ticker) params.append('ticker', filter.ticker)
      if (filter.signal) params.append('signal', filter.signal)

      const response = await axios.get<HistoryResponse>(`/api/v1/history?${params}`)
      setRecords(response.data.records)
      setPagination(prev => ({ ...prev, total: response.data.total }))
    } catch (err) {
      console.error('获取历史记录失败:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [pagination.limit, pagination.offset, filter])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSignalBadge = (signal: string) => {
    const styles = {
      BUY: 'bg-green-100 text-green-800 border-green-300',
      SELL: 'bg-red-100 text-red-800 border-red-300',
      HOLD: 'bg-yellow-100 text-yellow-800 border-yellow-300'
    }
    return styles[signal as keyof typeof styles] || ''
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">📜 历史记录</h1>

      {/* 筛选器 */}
      <div className="bg-white rounded-xl shadow-md p-4 mb-6">
        <div className="flex items-center space-x-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              股票代码
            </label>
            <input
              type="text"
              placeholder="例如: AAPL"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm uppercase"
              onChange={(e) => setFilter(prev => ({ ...prev, ticker: e.target.value || undefined }))}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              信号类型
            </label>
            <select
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              onChange={(e) => setFilter(prev => ({ ...prev, signal: e.target.value || undefined }))}
            >
              <option value="">全部</option>
              <option value="BUY">买入信号</option>
              <option value="SELL">卖出信号</option>
              <option value="HOLD">观望信号</option>
            </select>
          </div>
          <button
            onClick={() => setPagination(prev => ({ ...prev, offset: 0 }))}
            className="px-4 py-2 bg-turtle-600 text-white rounded-lg text-sm hover:bg-turtle-700"
          >
            筛选
          </button>
        </div>
      </div>

      {/* 历史记录表格 */}
      <div className="bg-white rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">时间</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">股票</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">价格</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">信号</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">N值</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">建议股数</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">状态</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    加载中...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    暂无历史记录
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(record.analysis_time)}
                    </td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-800">
                      {record.ticker}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-800">
                      ${record.current_price.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-semibold rounded border ${getSignalBadge(record.signal)}`}>
                        {record.signal}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {record.n_value ? `$${record.n_value.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {record.position_size ? record.position_size.toFixed(0) : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded ${record.is_active ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'}`}>
                        {record.is_active ? '活跃' : '已过期'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        <div className="bg-gray-50 px-4 py-3 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            共 {pagination.total} 条记录
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
              disabled={pagination.offset === 0}
              className="px-3 py-1 border rounded bg-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="text-sm text-gray-600">
              {Math.floor(pagination.offset / pagination.limit) + 1} / {Math.ceil(pagination.total / pagination.limit) || 1}
            </span>
            <button
              onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
              disabled={pagination.offset + pagination.limit >= pagination.total}
              className="px-3 py-1 border rounded bg-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
