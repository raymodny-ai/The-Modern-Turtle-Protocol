'use client'

import { useState } from 'react'
import { StockChart } from '@/app/components/StockChart'
import { SignalBadge } from '@/app/components/SignalBadge'
import { MetricsCard } from '@/app/components/MetricsCard'
import { PositionSection } from '@/app/components/PositionSection'
import axios from 'axios'

interface AnalysisResult {
  success: boolean
  ticker: string
  current_price: number
  previous_close: number | null
  price_change: number | null
  price_change_pct: number | null
  signal: 'BUY' | 'SELL' | 'HOLD'
  signal_reason: string
  channel_levels: {
    high_20_day: number | null
    low_10_day: number | null
  }
  volatility: {
    n_value: number | null
    dollar_volatility: number | null
    true_range_current: number | null
  }
  recommendation: {
    recommended_units: number
    position_size: number
    current_positions: number
    can_add_position: boolean
  }
  risk_metrics: {
    risk_percentage: number
    risk_amount: number
    max_position_value: number
  }
  price_history: Array<{
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
    high_20: number | null
    low_10: number | null
  }>
}

export default function AnalyzePage() {
  const [ticker, setTicker] = useState('')
  const [accountEquity, setAccountEquity] = useState('100000')
  const [period, setPeriod] = useState('1y')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async () => {
    if (!ticker.trim()) {
      setError('请输入股票代码')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post<AnalysisResult>('/api/v1/analyze', {
        ticker: ticker.trim().toUpperCase(),
        account_equity: parseFloat(accountEquity),
        period: period
      })
      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '分析失败，请稍后重试')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">📊 策略分析</h1>

      {/* 输入表单 */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-6">
        <div className="grid md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              股票代码
            </label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="例如: AAPL"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-turtle-500 focus:border-transparent uppercase"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              账户净资产 ($)
            </label>
            <input
              type="number"
              value={accountEquity}
              onChange={(e) => setAccountEquity(e.target.value)}
              min="0"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-turtle-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              数据周期
            </label>
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-turtle-500 focus:border-transparent"
            >
              <option value="1mo">1个月</option>
              <option value="3mo">3个月</option>
              <option value="6mo">6个月</option>
              <option value="1y">1年</option>
              <option value="2y">2年</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full bg-turtle-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-turtle-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  分析中...
                </span>
              ) : '开始分析'}
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-6">
          <strong>错误:</strong> {error}
        </div>
      )}

      {/* 分析结果 */}
      {result && result.success && (
        <div className="space-y-6 animate-fade-in">
          {/* 信号概览 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">{result.ticker}</h2>
                <p className="text-gray-500">
                  ${result.current_price.toFixed(2)}
                  {result.price_change_pct !== null && (
                    <span className={`ml-2 ${result.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {result.price_change_pct >= 0 ? '▲' : '▼'} {Math.abs(result.price_change_pct).toFixed(2)}%
                    </span>
                  )}
                </p>
              </div>
              <SignalBadge signal={result.signal} />
            </div>

            <div className="bg-turtle-50 rounded-lg p-4 mb-4">
              <p className="text-gray-700">{result.signal_reason}</p>
            </div>

            {/* 通道与波动率 */}
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <MetricsCard
                label="20日高点"
                value={result.channel_levels.high_20_day ? `$${result.channel_levels.high_20_day.toFixed(2)}` : '-'}
                subtext="入场阻力位"
              />
              <MetricsCard
                label="10日低点"
                value={result.channel_levels.low_10_day ? `$${result.channel_levels.low_10_day.toFixed(2)}` : '-'}
                subtext="出场支撑位"
              />
              <MetricsCard
                label="N值 (ATR)"
                value={result.volatility.n_value ? `$${result.volatility.n_value.toFixed(2)}` : '-'}
                subtext="20日平均真实波幅"
              />
              <MetricsCard
                label="美元波动率"
                value={result.volatility.dollar_volatility ? `$${result.volatility.dollar_volatility.toFixed(2)}` : '-'}
                subtext="每日预期波动"
              />
            </div>

            {/* 头寸建议 - 新增真实持仓窗口 */}
            <PositionSection 
              positionData={null}
              recommendation={result.recommendation}
            />
          </div>

          {/* 价格图表 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">📈 价格走势与通道</h3>
            <StockChart data={result.price_history} signal={result.signal} />
          </div>
        </div>
      )}
    </div>
  )
}
