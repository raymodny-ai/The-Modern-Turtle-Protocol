"""
投资组合风险管理系统
现代海龟协议 - 多层级风险敞口控制
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.core.config import settings
from app.database.models import PositionSnapshot, MarketCorrelation, SignalType
from sqlalchemy.orm import Session
import numpy as np


@dataclass
class RiskUnit:
    """风险单位"""
    ticker: str
    units: int
    n_value: float
    correlation_type: str  # HIGH, MEDIUM, LOW


@dataclass
class RiskCheckResult:
    """风险检查结果"""
    passed: bool
    blocked_reason: Optional[str] = None
    max_additional_units: int = 0
    current_exposure: int = 0
    limit_type: Optional[str] = None


class PortfolioRiskManager:
    """
    投资组合风险管理器
    
    风险控制层次:
    1. 单一市场限制 (4单位)
    2. 高关联市场限制 (6单位)
    3. 弱关联市场限制 (10单位)
    4. 单向总敞口限制 (12单位)
    """
    
    # 风险阈值常量
    SINGLE_MARKET_LIMIT = settings.SINGLE_MARKET_LIMIT          # 4
    HIGH_CORRELATION_LIMIT = settings.CLOSELY_CORRELATED_LIMIT  # 6
    LOW_CORRELATION_LIMIT = settings.LOOSELY_CORRELATED_LIMIT  # 10
    SINGLE_DIRECTION_LIMIT = settings.SINGLE_DIRECTION_LIMIT   # 12
    
    # 相关性阈值
    HIGH_CORRELATION_THRESHOLD = 0.7
    MEDIUM_CORRELATION_THRESHOLD = 0.4
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_risk_limits(
        self,
        ticker: str,
        proposed_direction: str = "LONG"
    ) -> RiskCheckResult:
        """
        检查风险限制
        
        执行四重拦截审查:
        1. 单一市场容量熔断
        2. 高关联市场熔断
        3. 弱关联市场熔断
        4. 单向总敞口熔断
        """
        # 获取当前组合状态
        current_positions = self._get_active_positions()
        correlations = self._get_correlations(ticker)
        
        # 1. 检查单一市场限制
        single_market_result = self._check_single_market_limit(ticker, current_positions)
        if not single_market_result.passed:
            return single_market_result
        
        # 2. 检查关联市场限制
        correlated_result = self._check_correlated_markets_limit(
            ticker, correlations, current_positions
        )
        if not correlated_result.passed:
            return correlated_result
        
        # 3. 检查单向总敞口限制
        direction_result = self._check_direction_limit(proposed_direction, current_positions)
        if not direction_result.passed:
            return direction_result
        
        # 所有检查通过
        return RiskCheckResult(
            passed=True,
            max_additional_units=self._calculate_max_units(ticker, current_positions),
            current_exposure=len(current_positions)
        )
    
    def _get_active_positions(self) -> List[PositionSnapshot]:
        """获取当前活跃持仓"""
        return self.db.query(PositionSnapshot).filter(
            PositionSnapshot.is_closed == False
        ).all()
    
    def _get_correlations(self, ticker: str) -> List[MarketCorrelation]:
        """获取与目标资产的关联资产"""
        return self.db.query(MarketCorrelation).filter(
            (MarketCorrelation.ticker_a == ticker) |
            (MarketCorrelation.ticker_b == ticker)
        ).all()
    
    def _check_single_market_limit(
        self,
        ticker: str,
        positions: List[PositionSnapshot]
    ) -> RiskCheckResult:
        """检查单一市场限制"""
        ticker_positions = [p for p in positions if p.ticker == ticker]
        current_units = sum(p.units for p in ticker_positions)
        
        if current_units >= self.SINGLE_MARKET_LIMIT:
            return RiskCheckResult(
                passed=False,
                blocked_reason=f"单一市场限制: {ticker} 已持有 {current_units} 单位，达到上限 {self.SINGLE_MARKET_LIMIT}",
                max_additional_units=0,
                current_exposure=current_units,
                limit_type="SINGLE_MARKET"
            )
        
        return RiskCheckResult(
            passed=True,
            max_additional_units=self.SINGLE_MARKET_LIMIT - current_units,
            current_exposure=current_units,
            limit_type="SINGLE_MARKET"
        )
    
    def _check_correlated_markets_limit(
        self,
        ticker: str,
        correlations: List[MarketCorrelation],
        positions: List[PositionSnapshot]
    ) -> RiskCheckResult:
        """检查关联市场限制"""
        if not correlations:
            # 无相关性数据，使用弱关联限制
            limit = self.LOW_CORRELATION_LIMIT
        else:
            # 计算最高关联类型
            max_correlation = max(abs(c.correlation) for c in correlations)
            
            if max_correlation >= self.HIGH_CORRELATION_THRESHOLD:
                limit = self.HIGH_CORRELATION_LIMIT
            elif max_correlation >= self.MEDIUM_CORRELATION_THRESHOLD:
                limit = self.LOW_CORRELATION_LIMIT
            else:
                limit = self.LOW_CORRELATION_LIMIT
        
        # 计算关联市场的总持仓
        correlated_tickers = set()
        for c in correlations:
            correlated_tickers.add(c.ticker_a)
            correlated_tickers.add(c.ticker_b)
        correlated_tickers.discard(ticker)
        
        correlated_units = sum(
            p.units for p in positions 
            if p.ticker in correlated_tickers
        )
        
        if correlated_units >= limit:
            return RiskCheckResult(
                passed=False,
                blocked_reason=f"关联市场限制: 关联资产已持有 {correlated_units} 单位，达到上限 {limit}",
                max_additional_units=0,
                current_exposure=correlated_units,
                limit_type="CORRELATED_MARKETS"
            )
        
        return RiskCheckResult(
            passed=True,
            max_additional_units=limit - correlated_units,
            current_exposure=correlated_units,
            limit_type="CORRELATED_MARKETS"
        )
    
    def _check_direction_limit(
        self,
        direction: str,
        positions: List[PositionSnapshot]
    ) -> RiskCheckResult:
        """检查单向总敞口限制"""
        direction_positions = [
            p for p in positions 
            if p.position_type == direction
        ]
        direction_units = sum(p.units for p in direction_positions)
        
        if direction_units >= self.SINGLE_DIRECTION_LIMIT:
            return RiskCheckResult(
                passed=False,
                blocked_reason=f"单向敞口限制: {direction} 方向已持有 {direction_units} 单位，达到上限 {self.SINGLE_DIRECTION_LIMIT}",
                max_additional_units=0,
                current_exposure=direction_units,
                limit_type="SINGLE_DIRECTION"
            )
        
        return RiskCheckResult(
            passed=True,
            max_additional_units=self.SINGLE_DIRECTION_LIMIT - direction_units,
            current_exposure=direction_units,
            limit_type="SINGLE_DIRECTION"
        )
    
    def _calculate_max_units(
        self,
        ticker: str,
        positions: List[PositionSnapshot]
    ) -> int:
        """计算最大可添加单位数"""
        # 单一市场剩余容量
        ticker_units = sum(p.units for p in positions if p.ticker == ticker)
        single_market_remaining = max(0, self.SINGLE_MARKET_LIMIT - ticker_units)
        
        # 单向剩余容量
        direction_units = sum(
            p.units for p in positions 
            if p.position_type == "LONG"
        )
        direction_remaining = max(0, self.SINGLE_DIRECTION_LIMIT - direction_units)
        
        return min(single_market_remaining, direction_remaining)
    
    def calculate_correlation(
        self,
        ticker_a: str,
        ticker_b: str,
        returns_a: np.ndarray,
        returns_b: np.ndarray
    ) -> Tuple[float, str]:
        """
        计算两个资产间的皮尔逊相关系数
        
        Returns:
            (correlation, correlation_type)
        """
        if len(returns_a) != len(returns_b) or len(returns_a) < 10:
            return 0.0, "LOW"
        
        # 计算皮尔逊相关系数
        correlation = np.corrcoef(returns_a, returns_b)[0, 1]
        
        # 确定关联类型
        abs_corr = abs(correlation)
        if abs_corr >= self.HIGH_CORRELATION_THRESHOLD:
            corr_type = "HIGH"
        elif abs_corr >= self.MEDIUM_CORRELATION_THRESHOLD:
            corr_type = "MEDIUM"
        else:
            corr_type = "LOW"
        
        return correlation, corr_type
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合风险摘要"""
        positions = self._get_active_positions()
        
        # 按方向汇总
        long_units = sum(p.units for p in positions if p.position_type == "LONG")
        short_units = sum(p.units for p in positions if p.position_type == "SHORT")
        
        # 按资产汇总
        by_ticker = {}
        for p in positions:
            if p.ticker not in by_ticker:
                by_ticker[p.ticker] = {'units': 0, 'positions': []}
            by_ticker[p.ticker]['units'] += p.units
            by_ticker[p.ticker]['positions'].append(p.id)
        
        # 风险指标
        total_exposure = long_units + short_units
        net_exposure = long_units - short_units
        
        return {
            'total_positions': len(positions),
            'total_exposure': total_exposure,
            'long_units': long_units,
            'short_units': short_units,
            'net_exposure': net_exposure,
            'by_ticker': by_ticker,
            'limits': {
                'single_market': self.SINGLE_MARKET_LIMIT,
                'high_correlation': self.HIGH_CORRELATION_LIMIT,
                'low_correlation': self.LOW_CORRELATION_LIMIT,
                'single_direction': self.SINGLE_DIRECTION_LIMIT
            },
            'utilization': {
                'long': round(long_units / self.SINGLE_DIRECTION_LIMIT * 100, 2),
                'short': round(short_units / self.SINGLE_DIRECTION_LIMIT * 100, 2)
            }
        }
