'use client'

interface PositionData {
  has_position: boolean
  units: number
  shares: number
  avg_entry_price: number | null
  position_type: string | null
  is_closed: boolean
  opened_at: string | null
}

interface Recommendation {
  recommended_units: number
  position_size: number
  current_positions: number
  can_add_position: boolean
}

interface PositionSectionProps {
  positionData: PositionData | null
  recommendation: Recommendation
}

export function PositionSection({ positionData, recommendation }: PositionSectionProps) {
  // 如果没有真实持仓数据，展示建议
  if (!positionData) {
    return (
      <div className="border-t pt-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">💰 头寸建议</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-turtle-50 rounded-lg p-4 border border-turtle-200">
            <div className="text-sm text-turtle-600 mb-1">建议单位</div>
            <div className="text-2xl font-bold text-turtle-800">
              {recommendation.recommended_units.toFixed(2)}
            </div>
            <div className="text-xs text-turtle-500 mt-1">基于1%风险</div>
          </div>
          <div className="bg-turtle-50 rounded-lg p-4 border border-turtle-200">
            <div className="text-sm text-turtle-600 mb-1">建议股数</div>
            <div className="text-2xl font-bold text-turtle-800">
              {recommendation.position_size.toFixed(0)}
            </div>
            <div className="text-xs text-turtle-500 mt-1">可买入股数</div>
          </div>
          <div className="bg-gray-100 rounded-lg p-4 border border-gray-200">
            <div className="text-sm text-gray-600 mb-1">当前持仓</div>
            <div className="text-2xl font-bold text-gray-400">-</div>
            <div className="text-xs text-gray-500 mt-1">暂无持仓数据</div>
          </div>
        </div>
      </div>
    )
  }

  const { has_position, units, shares, avg_entry_price, position_type, is_closed } = positionData

  return (
    <div className="border-t pt-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">💼 持仓信息</h3>
      
      {/* 两列布局：左侧真实持仓，右侧系统建议 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* 左侧：真实持仓 */}
        <div className={`rounded-lg p-4 border ${
          has_position 
            ? 'bg-green-50 border-green-200' 
            : 'bg-gray-50 border-gray-200'
        }`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">当前真实持仓</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              has_position 
                ? 'bg-green-100 text-green-700' 
                : 'bg-gray-200 text-gray-600'
            }`}>
              {has_position ? '已持仓' : '空仓'}
            </span>
          </div>
          
          {has_position ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">持仓方向</span>
                <span className={`font-semibold ${
                  position_type === 'LONG' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {position_type === 'LONG' ? '📈 多头' : '📉 空头'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">风险单位</span>
                <span className="font-semibold text-gray-800">{units}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">持仓股数</span>
                <span className="font-semibold text-gray-800">{shares.toFixed(0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">平均入场价</span>
                <span className="font-semibold text-gray-800">
                  {avg_entry_price ? `$${avg_entry_price.toFixed(2)}` : '-'}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-4 text-gray-500">
              <div className="text-3xl mb-2">🌊</div>
              <p className="text-sm">暂无持仓</p>
              <p className="text-xs text-gray-400 mt-1">可考虑建仓</p>
            </div>
          )}
        </div>

        {/* 右侧：系统建议 */}
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-700">系统建议</span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              recommendation.can_add_position 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-yellow-100 text-yellow-700'
            }`}>
              {recommendation.can_add_position ? '可加仓' : '已达上限'}
            </span>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">建议单位</span>
              <span className="font-semibold text-blue-800">{recommendation.recommended_units.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">建议股数</span>
              <span className="font-semibold text-blue-800">{recommendation.position_size.toFixed(0)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">当前持仓</span>
              <span className="font-semibold text-blue-800">{recommendation.current_positions}</span>
            </div>
            <div className="flex justify-between items-center pt-2 border-t border-blue-200">
              <span className="text-sm font-medium text-blue-700">还可增加</span>
              <span className={`font-bold ${
                recommendation.can_add_position ? 'text-green-600' : 'text-gray-400'
              }`}>
                {Math.max(0, recommendation.recommended_units - recommendation.current_positions).toFixed(2)} 单位
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 持仓状态说明 */}
      <div className="mt-4 text-xs text-gray-500 bg-gray-50 rounded-lg p-3">
        <p className="mb-1">
          <strong>说明：</strong>
        </p>
        <ul className="list-disc list-inside space-y-0.5">
          <li><strong>当前真实持仓</strong>：从数据库读取的实际账户持仓状态</li>
          <li><strong>系统建议</strong>：基于当前市场波动率和账户净资产计算的建议仓位</li>
          <li><strong>还可增加</strong>：建议单位 - 当前持仓，反映可加仓空间</li>
        </ul>
      </div>
    </div>
  )
}
