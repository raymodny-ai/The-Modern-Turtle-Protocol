"""
SQLAlchemy ORM模型定义
现代海龟协议 - 数据库实体模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, Text, Index
from sqlalchemy.sql import func
from app.database.session import Base
import enum


class SignalType(str, enum.Enum):
    """交易信号枚举类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AnalysisRecord(Base):
    """策略分析记录表 - 存储每次分析的历史数据"""
    __tablename__ = "analysis_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 基础信息
    ticker = Column(String(20), nullable=False, index=True, comment="资产代码")
    analysis_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="分析时间")
    
    # 价格数据
    current_price = Column(Float, nullable=False, comment="当前收盘价")
    entry_price = Column(Float, nullable=True, comment="入场价格(如有持仓)")
    exit_price = Column(Float, nullable=True, comment="出场价格")
    
    # 策略信号
    signal = Column(Enum(SignalType), nullable=False, comment="交易信号")
    signal_reason = Column(Text, nullable=True, comment="信号生成原因")
    
    # 通道参数
    high_20_day = Column(Float, nullable=True, comment="20日最高价")
    low_10_day = Column(Float, nullable=True, comment="10日最低价")
    
    # 波动率参数
    n_value = Column(Float, nullable=True, comment="N值(ATR)")
    dollar_volatility = Column(Float, nullable=True, comment="美元波动率")
    
    # 头寸计算
    account_equity = Column(Float, nullable=False, comment="账户净资产")
    risk_amount = Column(Float, nullable=True, comment="风险金额(1%)")
    recommended_units = Column(Float, nullable=True, comment="建议交易单位")
    dollar_per_point = Column(Float, default=1.0, comment="每点美元价值")
    
    # 持仓信息
    position_size = Column(Float, nullable=True, comment="建议持仓股数")
    current_positions = Column(Integer, default=0, comment="当前持仓单位数")
    
    # 元数据
    is_active = Column(Boolean, default=True, comment="是否活跃信号")
    error_message = Column(Text, nullable=True, comment="错误信息(如分析失败)")
    
    # 索引优化
    __table_args__ = (
        Index('idx_ticker_analysis_time', 'ticker', 'analysis_time'),
        Index('idx_signal_type', 'signal'),
        Index('idx_analysis_time', 'analysis_time'),
    )
    
    def __repr__(self):
        return f"<AnalysisRecord(ticker={self.ticker}, signal={self.signal}, n_value={self.n_value})>"


class PositionSnapshot(Base):
    """持仓快照表 - 记录投资组合当前状态"""
    __tablename__ = "position_snapshots"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 持仓基础信息
    ticker = Column(String(20), nullable=False, index=True, comment="资产代码")
    position_type = Column(String(10), nullable=False, comment="持仓类型(LONG/SHORT)")
    
    # 持仓数量
    units = Column(Integer, default=0, comment="风险单位数")
    shares = Column(Float, nullable=True, comment="持仓股数")
    avg_entry_price = Column(Float, nullable=True, comment="平均入场价")
    
    # 风险参数
    n_value_at_entry = Column(Float, nullable=True, comment="入场时N值")
    stop_loss_price = Column(Float, nullable=True, comment="止损价格")
    risk_per_unit = Column(Float, nullable=True, comment="每单位风险金额")
    
    # 时间戳
    opened_at = Column(DateTime(timezone=True), nullable=False, comment="开仓时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    closed_at = Column(DateTime(timezone=True), nullable=True, comment="平仓时间")
    
    # 状态
    is_closed = Column(Boolean, default=False, comment="是否已平仓")
    
    __table_args__ = (
        Index('idx_ticker_status', 'ticker', 'is_closed'),
    )
    
    def __repr__(self):
        return f"<PositionSnapshot(ticker={self.ticker}, units={self.units})>"


class MarketCorrelation(Base):
    """市场关联度表 - 存储资产相关性矩阵"""
    __tablename__ = "market_correlations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联资产对
    ticker_a = Column(String(20), nullable=False, index=True, comment="资产A代码")
    ticker_b = Column(String(20), nullable=False, index=True, comment="资产B代码")
    
    # 相关性参数
    correlation = Column(Float, nullable=False, comment="皮尔逊相关系数(-1到1)")
    correlation_type = Column(String(20), nullable=False, comment="关联类型(HIGH/MEDIUM/LOW)")
    
    # 计算信息
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), comment="计算时间")
    data_period = Column(Integer, default=30, comment="数据周期(天)")
    
    # 有效期
    valid_until = Column(DateTime(timezone=True), nullable=True, comment="有效期至")
    
    __table_args__ = (
        Index('idx_ticker_pair', 'ticker_a', 'ticker_b', unique=True),
    )
    
    def __repr__(self):
        return f"<MarketCorrelation({self.ticker_a}-{self.ticker_b}: {self.correlation})>"


class NotificationLog(Base):
    """通知日志表 - 记录所有发出的通知"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联分析记录
    analysis_id = Column(Integer, nullable=True, index=True, comment="关联分析ID")
    
    # 通知类型
    notification_type = Column(String(20), nullable=False, comment="通知类型(EMAIL/WEBHOOK)")
    signal = Column(Enum(SignalType), nullable=False, comment="触发信号")
    
    # 通知内容
    subject = Column(String(200), nullable=True, comment="通知主题")
    message = Column(Text, nullable=False, comment="通知内容")
    
    # 发送状态
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="发送时间")
    status = Column(String(20), default="PENDING", comment="发送状态(PENDING/SENT/FAILED)")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 目标
    recipients = Column(Text, nullable=True, comment="接收者列表(JSON)")
    
    def __repr__(self):
        return f"<NotificationLog(type={self.notification_type}, signal={self.signal})>"
