"""
Pydantic数据校验模型
现代海龟协议 - API请求与响应数据结构
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """交易信号枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class CorrelationType(str, Enum):
    """关联度类型"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================
# 请求模型
# ============================================

class AnalyzeRequest(BaseModel):
    """策略分析请求模型"""
    ticker: str = Field(
        ..., 
        min_length=1, 
        max_length=20,
        description="资产交易代码，如AAPL、EURUSD",
        examples=["AAPL", "GOOGL", "MSFT"]
    )
    account_equity: float = Field(
        ..., 
        gt=0,
        description="账户总净资产(必须大于0)",
        examples=[100000.0, 500000.0]
    )
    period: str = Field(
        default="1y",
        description="历史数据周期(1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
        examples=["1y", "6mo"]
    )
    dollar_per_point: float = Field(
        default=1.0,
        gt=0,
        description="每点美元价值(股票默认1.0，外汇/期货需配置)",
        examples=[1.0, 10.0]
    )
    
    @field_validator('ticker')
    @classmethod
    def ticker_uppercase(cls, v: str) -> str:
        """自动将ticker转换为大写"""
        return v.upper().strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "account_equity": 100000.0,
                "period": "1y",
                "dollar_per_point": 1.0
            }
        }


class HistoryQuery(BaseModel):
    """历史记录查询模型"""
    ticker: Optional[str] = Field(None, description="资产代码过滤")
    signal: Optional[SignalType] = Field(None, description="信号类型过滤")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    limit: int = Field(default=50, ge=1, le=500, description="返回记录数")
    offset: int = Field(default=0, ge=0, description="分页偏移量")


class PositionAddRequest(BaseModel):
    """添加持仓请求模型"""
    ticker: str = Field(..., min_length=1, max_length=20, description="资产代码")
    position_type: Literal["LONG", "SHORT"] = Field(..., description="持仓类型")
    shares: float = Field(..., gt=0, description="持仓股数")
    entry_price: float = Field(..., gt=0, description="入场价格")
    n_value: float = Field(..., gt=0, description="入场时N值")


# ============================================
# 响应模型
# ============================================

class PriceData(BaseModel):
    """价格数据点"""
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChannelLevels(BaseModel):
    """通道水平"""
    high_20_day: float = Field(description="20日最高价(入场阻力)")
    low_10_day: float = Field(description="10日最低价(出场支撑)")


class VolatilityData(BaseModel):
    """波动率数据"""
    n_value: float = Field(description="N值(ATR)")
    dollar_volatility: float = Field(description="美元波动率")
    true_range_current: float = Field(description="当前真实波幅")


class RiskMetrics(BaseModel):
    """风险指标"""
    risk_percentage: float = Field(description="风险百分比(1%)")
    risk_amount: float = Field(description="风险金额(美元)")
    max_position_value: float = Field(description="最大持仓市值")


class PositionRecommendation(BaseModel):
    """持仓建议"""
    recommended_units: float = Field(description="建议交易单位数")
    position_size: float = Field(description="建议持仓股数/合约数")
    current_positions: int = Field(default=0, description="当前持仓单位数")
    can_add_position: bool = Field(description="是否可以加仓")


class SignalDetail(BaseModel):
    """信号详情"""
    signal: SignalType
    signal_reason: str
    price_action: str


class AnalyzeResponse(BaseModel):
    """策略分析响应模型"""
    success: bool = Field(description="分析是否成功")
    ticker: str = Field(description="资产代码")
    analysis_time: datetime = Field(description="分析时间")
    
    # 价格信息
    current_price: float = Field(description="当前收盘价")
    previous_close: Optional[float] = Field(None, description="前一交易日收盘价")
    price_change: Optional[float] = Field(None, description="价格变动")
    price_change_pct: Optional[float] = Field(None, description="价格变动百分比")
    
    # 策略信号
    signal: SignalType = Field(description="交易信号")
    signal_detail: SignalDetail = Field(description="信号详情")
    
    # 通道参数
    channel_levels: ChannelLevels = Field(description="通道水平")
    
    # 波动率
    volatility: VolatilityData = Field(description="波动率数据")
    
    # 头寸建议
    recommendation: PositionRecommendation = Field(description="持仓建议")
    
    # 风险指标
    risk_metrics: RiskMetrics = Field(description="风险指标")
    
    # 图表数据
    price_history: List[PriceData] = Field(description="历史价格数据(用于图表)")
    
    # 错误信息(如分析失败)
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ticker": "AAPL",
                "analysis_time": "2024-01-15T10:30:00Z",
                "current_price": 185.50,
                "signal": "BUY",
                "n_value": 3.25,
                "recommended_units": 3.0,
                "position_size": 57.0
            }
        }


class HistoryRecord(BaseModel):
    """历史分析记录"""
    id: int
    ticker: str
    analysis_time: datetime
    current_price: float
    signal: SignalType
    signal_reason: Optional[str] = None
    high_20_day: Optional[float] = None
    low_10_day: Optional[float] = None
    n_value: Optional[float] = None
    recommended_units: Optional[float] = None
    position_size: Optional[float] = None
    account_equity: float
    is_active: bool = True
    
    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    """历史记录响应"""
    success: bool = True
    total: int = Field(description="总记录数")
    limit: int
    offset: int
    records: List[HistoryRecord] = Field(description="历史记录列表")


class PositionResponse(BaseModel):
    """持仓响应"""
    id: int
    ticker: str
    position_type: str
    units: int
    shares: Optional[float] = None
    avg_entry_price: Optional[float] = None
    n_value_at_entry: Optional[float] = None
    stop_loss_price: Optional[float] = None
    opened_at: datetime
    is_closed: bool
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    current_price: Optional[float] = Field(None, description="当前价格")
    
    class Config:
        from_attributes = True


class CorrelationInfo(BaseModel):
    """相关性信息"""
    ticker_a: str
    ticker_b: str
    correlation: float = Field(ge=-1.0, le=1.0)
    correlation_type: CorrelationType
    calculated_at: datetime


class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str
    database: str
    data_sources: dict
    last_update: datetime


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
