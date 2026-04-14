"""
策略运算与信号生成模块
现代海龟协议 - 核心趋势跟踪策略实现
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List
from datetime import datetime
from app.core.config import settings


class SignalType:
    """交易信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TurtleStrategy:
    """
    现代海龟协议趋势跟踪策略
    
    核心逻辑:
    - 入场信号: 价格突破20日最高价 → BUY
    - 出场信号: 价格跌破10日最低价 → SELL
    - 无信号: 价格在通道内震荡 → HOLD
    
    参数:
    - entry_period: 入场周期(默认20日)
    - exit_period: 出场周期(默认10日)
    """
    
    def __init__(
        self,
        entry_period: int = None,
        exit_period: int = None,
        atr_period: int = None
    ):
        self.entry_period = entry_period or settings.ENTRY_PERIOD
        self.exit_period = exit_period or settings.EXIT_PERIOD
        self.atr_period = atr_period or settings.ATR_PERIOD
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算策略所需的技术指标
        
        Args:
            df: 包含OHLCV数据的DataFrame
            
        Returns:
            添加了技术指标的DataFrame
        """
        data = df.copy()
        
        # 1. 计算真实波幅 (True Range)
        data['TR'] = self._calculate_true_range(data)
        
        # 2. 计算N值 (ATR - Average True Range)
        data['N'] = data['TR'].ewm(alpha=1.0/self.atr_period, adjust=False).mean()
        
        # 3. 计算20日最高价 (入场阻力位)
        data['High_20'] = data['High'].rolling(window=self.entry_period).max()
        
        # 4. 计算10日最低价 (出场支撑位)
        data['Low_10'] = data['Low'].rolling(window=self.exit_period).min()
        
        # 5. 计算移动平均 (用于参考)
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_10'] = data['Close'].rolling(window=10).mean()
        
        # 6. 计算波动率标准化指标
        data['Volatility_Ratio'] = data['N'] / data['Close']
        
        return data
    
    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """
        计算真实波幅 (True Range)
        
        TR = max(
            当日最高价 - 当日最低价,
            |当日最高价 - 前一收盘价|,
            |当日最低价 - 前一收盘价|
        )
        """
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr
    
    def generate_signal(
        self, 
        data: pd.DataFrame
    ) -> Tuple[str, str, dict]:
        """
        生成交易信号
        
        Args:
            data: 包含指标数据的DataFrame
            
        Returns:
            (signal, reason, details)
        """
        # 获取最新数据点
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        current_price = latest['Close']
        high_20 = latest['High_20']
        low_10 = latest['Low_10']
        n_value = latest['N']
        
        # 确保有足够的历史数据
        if pd.isna(high_20) or pd.isna(low_10) or pd.isna(n_value):
            return SignalType.HOLD, "历史数据不足，无法生成信号", {
                'current_price': current_price,
                'high_20_day': None,
                'low_10_day': None,
                'n_value': None
            }
        
        # 信号判断逻辑
        # BUY: 价格向上突破20日最高价
        if current_price > high_20:
            signal = SignalType.BUY
            reason = f"价格(${current_price:.2f})向上突破20日最高价(${high_20:.2f})，触发入场信号"
            price_action = f"突破入场: 当前价 > 20日高点"
            
        # SELL: 价格向下突破10日最低价
        elif current_price < low_10:
            signal = SignalType.SELL
            reason = f"价格(${current_price:.2f})向下突破10日最低价(${low_10:.2f})，触发出场信号"
            price_action = f"突破出场: 当前价 < 10日低点"
            
        # HOLD: 价格在通道内震荡
        else:
            signal = SignalType.HOLD
            if current_price > latest['SMA_20']:
                reason = f"价格在通道内运行，当前价(${current_price:.2f})高于20日均线"
                price_action = "震荡整理: 区间波动"
            else:
                reason = f"价格在通道内运行，等待突破确认"
                price_action = "震荡整理: 区间波动"
        
        details = {
            'current_price': current_price,
            'previous_price': prev['Close'],
            'high_20_day': high_20,
            'low_10_day': low_10,
            'n_value': n_value,
            'sma_20': latest['SMA_20'],
            'volatility_ratio': latest['Volatility_Ratio'],
            'price_action': price_action,
            'entry_breakout': high_20,
            'exit_breakdown': low_10
        }
        
        return signal, reason, details
    
    def get_channel_levels(self, data: pd.DataFrame) -> dict:
        """获取通道水平"""
        latest = data.iloc[-1]
        return {
            'high_20_day': latest['High_20'] if not pd.isna(latest['High_20']) else None,
            'low_10_day': latest['Low_10'] if not pd.isna(latest['Low_10']) else None
        }
    
    def get_volatility_data(self, data: pd.DataFrame, dollar_per_point: float = 1.0) -> dict:
        """获取波动率数据"""
        latest = data.iloc[-1]
        prev_n = data['N'].iloc[-2] if len(data) > 1 else latest['N']
        
        # N值
        n_value = latest['N'] if not pd.isna(latest['N']) else None
        
        # 美元波动率 = N值 × 每点美元价值 × 合约乘数
        # 符合PRD第4.2章要求：dollar_volatility = N × dollar_per_point
        dollar_volatility = n_value * dollar_per_point if n_value else None
        
        return {
            'n_value': n_value,
            'dollar_volatility': dollar_volatility,
            'dollar_per_point': dollar_per_point,
            'true_range_current': latest['TR'] if not pd.isna(latest['TR']) else None,
            'n_change': ((latest['N'] - prev_n) / prev_n * 100) if not pd.isna(prev_n) and prev_n > 0 else 0,
            'volatility_percentile': self._calculate_volatility_percentile(data)
        }
    
    def _calculate_volatility_percentile(self, data: pd.DataFrame, window: int = 60) -> float:
        """计算波动率历史百分位"""
        if len(data) < window:
            return 50.0
        
        recent_n = data['N'].iloc[-window:]
        current_n = data['N'].iloc[-1]
        
        percentile = (recent_n < current_n).sum() / len(recent_n) * 100
        return round(percentile, 2)


class TurtleStrategyAnalyzer:
    """
    海龟策略分析器
    整合数据获取、指标计算、信号生成和头寸计算
    """
    
    def __init__(self):
        self.strategy = TurtleStrategy()
    
    def analyze(
        self,
        df: pd.DataFrame,
        account_equity: float,
        dollar_per_point: float = 1.0
    ) -> dict:
        """
        完整分析流程
        
        Args:
            df: OHLCV数据
            account_equity: 账户净资产
            dollar_per_point: 每点美元价值
            
        Returns:
            完整的分析结果字典
        """
        # 1. 计算技术指标
        data = self.strategy.calculate_indicators(df)
        
        # 2. 生成交易信号
        signal, reason, details = self.strategy.generate_signal(data)
        
        # 3. 计算波动率参数
        volatility = self.strategy.get_volatility_data(data, dollar_per_point)
        n_value = volatility['n_value'] or 0
        
        # 4. 计算头寸规模
        position_calc = self._calculate_position_size(
            account_equity=account_equity,
            n_value=n_value,
            dollar_per_point=dollar_per_point
        )
        
        # 5. 获取通道水平
        channels = self.strategy.get_channel_levels(data)
        
        # 6. 准备价格历史数据
        price_history = self._prepare_price_history(data)
        
        # 构建完整响应
        return {
            'success': True,
            'signal': signal,
            'signal_reason': reason,
            'signal_detail': {
                'signal': signal,
                'signal_reason': reason,
                'price_action': details.get('price_action', '')
            },
            'current_price': details['current_price'],
            'previous_close': details.get('previous_price'),
            'channel_levels': channels,
            'volatility': volatility,
            'position': position_calc,
            'risk_metrics': {
                'risk_percentage': settings.RISK_PERCENTAGE * 100,
                'risk_amount': account_equity * settings.RISK_PERCENTAGE,
                'max_position_value': position_calc.get('max_position_value', 0)
            },
            'price_history': price_history,
            'indicators': {
                'n_value': n_value,
                'high_20_day': channels['high_20_day'],
                'low_10_day': channels['low_10_day'],
                'sma_20': details.get('sma_20'),
                'volatility_ratio': details.get('volatility_ratio')
            }
        }
    
    def _calculate_position_size(
        self,
        account_equity: float,
        n_value: float,
        dollar_per_point: float = 1.0
    ) -> dict:
        """
        计算头寸规模
        
        公式: Units = (账户净资产 × 0.01) / (N值 × 每点美元价值)
        """
        if n_value <= 0:
            return {
                'recommended_units': 0,
                'position_size': 0,
                'risk_amount': 0,
                'dollar_volatility': 0,
                'max_position_value': 0,
                'can_add_position': False
            }
        
        # 计算风险金额 (1%)
        risk_amount = account_equity * settings.RISK_PERCENTAGE
        
        # 计算美元波动率 (N值 × 每点美元价值)
        dollar_volatility = n_value * dollar_per_point
        
        # 计算建议单位数
        recommended_units = risk_amount / dollar_volatility if dollar_volatility > 0 else 0
        
        # 计算建议持仓股数
        position_size = recommended_units  # 股票场景下，1单位=1股
        
        # 最大持仓市值
        max_position_value = recommended_units * n_value * dollar_per_point
        
        return {
            'recommended_units': round(recommended_units, 2),
            'position_size': round(position_size, 2),
            'risk_amount': round(risk_amount, 2),
            'dollar_volatility': round(dollar_volatility, 2),
            'max_position_value': round(max_position_value, 2),
            'can_add_position': recommended_units > 0,
            'dollar_per_point': dollar_per_point
        }
    
    def _prepare_price_history(self, data: pd.DataFrame) -> List[dict]:
        """准备价格历史数据用于图表"""
        # 返回最近60个交易日的数据
        recent_data = data.tail(60)
        
        return [
            {
                'date': idx.to_pydatetime(),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': float(row['Volume']),
                'high_20': float(row['High_20']) if not pd.isna(row['High_20']) else None,
                'low_10': float(row['Low_10']) if not pd.isna(row['Low_10']) else None,
                'sma_20': float(row['SMA_20']) if not pd.isna(row['SMA_20']) else None
            }
            for idx, row in recent_data.iterrows()
        ]


# 全局策略分析器实例
strategy_analyzer = TurtleStrategyAnalyzer()


def analyze_turtle_strategy(
    df: pd.DataFrame,
    account_equity: float,
    dollar_per_point: float = 1.0
) -> dict:
    """便捷分析函数"""
    return strategy_analyzer.analyze(df, account_equity, dollar_per_point)
