/**
 * API客户端模块
 * 现代海龟协议量化交易系统前端API调用封装
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

// API配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1'

// 创建Axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加请求日志
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一错误处理
    if (error.response) {
      const message = error.response.data?.detail || error.response.data?.error || '请求失败'
      console.error(`[API Error] ${error.response.status}: ${message}`)
      return Promise.reject(new Error(message))
    } else if (error.request) {
      console.error('[API Error] 网络连接失败')
      return Promise.reject(new Error('网络连接失败，请检查网络'))
    }
    return Promise.reject(error)
  }
)

// ==================== 类型定义 ====================

export interface AnalyzeRequest {
  ticker: string
  account_equity: number
  period?: string
  dollar_per_point?: number
}

export interface AnalyzeResponse {
  success: boolean
  ticker: string
  analysis_time: string
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
  price_history: PriceData[]
}

export interface PriceData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  high_20: number | null
  low_10: number | null
}

export interface HistoryRecord {
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

export interface HistoryResponse {
  success: boolean
  total: number
  limit: number
  offset: number
  records: HistoryRecord[]
}

export interface Position {
  id: number
  ticker: string
  position_type: 'LONG' | 'SHORT'
  units: number
  shares: number | null
  avg_entry_price: number | null
  n_value_at_entry: number | null
  stop_loss_price: number | null
  opened_at: string
  is_closed: boolean
}

export interface PortfolioSummary {
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

// ==================== API函数 ====================

export const tradingApi = {
  /**
   * 执行策略分析
   */
  analyze: async (data: AnalyzeRequest): Promise<AnalyzeResponse> => {
    const response = await apiClient.post<AnalyzeResponse>('/analyze', data)
    return response.data
  },

  /**
   * 获取历史记录
   */
  getHistory: async (params?: {
    ticker?: string
    signal?: string
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }): Promise<HistoryResponse> => {
    const response = await apiClient.get<HistoryResponse>('/history', { params })
    return response.data
  },

  /**
   * 获取信号统计
   */
  getStatistics: async (params?: {
    ticker?: string
    days?: number
  }): Promise<any> => {
    const response = await apiClient.get('/history/statistics', { params })
    return response.data
  },

  /**
   * 获取持仓列表
   */
  getPositions: async (params?: {
    ticker?: string
    include_closed?: boolean
  }): Promise<Position[]> => {
    const response = await apiClient.get<Position[]>('/positions', { params })
    return response.data
  },

  /**
   * 添加持仓
   */
  addPosition: async (data: {
    ticker: string
    position_type: 'LONG' | 'SHORT'
    shares: number
    entry_price: number
    n_value: number
  }): Promise<{ success: boolean; position_id: number }> => {
    const response = await apiClient.post('/positions', data)
    return response.data
  },

  /**
   * 平仓
   */
  closePosition: async (positionId: number, exitPrice: number): Promise<any> => {
    const response = await apiClient.post(`/positions/${positionId}/close`, { exit_price: exitPrice })
    return response.data
  },

  /**
   * 获取投资组合摘要
   */
  getPortfolioSummary: async (): Promise<PortfolioSummary> => {
    const response = await apiClient.get<PortfolioSummary>('/positions/summary')
    return response.data
  },
}

export default apiClient
