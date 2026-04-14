"""
策略回测断言套件
PRD第2.3章要求: 自动化API端点测试与策略回测断言套件
"""

import pytest
import pandas as pd
import numpy as np
from app.services.strategy import TurtleStrategy, TurtleStrategyAnalyzer
from app.database.models import PositionSnapshot, SignalType


class TestTurtleStrategy:
    """海龟策略单元测试"""
    
    @pytest.fixture
    def sample_data(self):
        """生成测试用OHLCV数据"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # 生成模拟价格数据
        prices = 100 + np.cumsum(np.random.randn(100) * 2)
        
        data = pd.DataFrame({
            'Open': prices + np.random.randn(100) * 0.5,
            'High': prices + abs(np.random.randn(100) * 2),
            'Low': prices - abs(np.random.randn(100) * 2),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100)
        }, index=dates)
        
        return data
    
    def test_calculate_true_range(self, sample_data):
        """测试真实波幅计算"""
        strategy = TurtleStrategy()
        tr = strategy._calculate_true_range(sample_data)
        
        assert len(tr) == len(sample_data)
        assert (tr >= 0).all()  # TR必须非负
    
    def test_calculate_indicators(self, sample_data):
        """测试指标计算"""
        strategy = TurtleStrategy()
        data = strategy.calculate_indicators(sample_data)
        
        assert 'TR' in data.columns
        assert 'N' in data.columns
        assert 'High_20' in data.columns
        assert 'Low_10' in data.columns
        
        # 前19行应该没有High_20值
        assert pd.isna(data['High_20'].iloc[18])
        assert not pd.isna(data['High_20'].iloc[-1])
    
    def test_signal_generation(self, sample_data):
        """测试信号生成"""
        strategy = TurtleStrategy()
        data = strategy.calculate_indicators(sample_data)
        
        signal, reason, details = strategy.generate_signal(data)
        
        assert signal in ['BUY', 'SELL', 'HOLD']
        assert isinstance(reason, str)
        assert 'current_price' in details
        assert 'n_value' in details
    
    def test_channel_levels(self, sample_data):
        """测试通道水平计算"""
        strategy = TurtleStrategy()
        data = strategy.calculate_indicators(sample_data)
        
        channels = strategy.get_channel_levels(data)
        
        assert 'high_20_day' in channels
        assert 'low_10_day' in channels
        if channels['high_20_day'] and channels['low_10_day']:
            assert channels['high_20_day'] >= channels['low_10_day']


class TestPositionCalculation:
    """头寸计算测试 - 修复Bug: Unit需转换为实际股数"""
    
    def test_unit_size_calculation(self):
        """测试单位规模计算(风险单位)"""
        analyzer = TurtleStrategyAnalyzer()
        
        result = analyzer._calculate_position_size(
            account_equity=100000,
            n_value=2.5,
            dollar_per_point=1.0,
            current_price=100.0  # 股票价格
        )
        
        # 100000 * 0.01 = 1000 风险金额
        # 1000 / (2.5 * 1) = 400 风险单位
        expected_units = 1000 / (2.5 * 1)
        # 股数 = 400 * (2.5 / 100) = 10股
        expected_shares = expected_units * (2.5 / 100.0)
        
        assert result['recommended_units'] == pytest.approx(expected_units, rel=0.01)
        assert result['position_size'] == pytest.approx(expected_shares, rel=0.01)
        assert result['risk_amount'] == 1000.0
        assert result['dollar_volatility'] == 2.5
    
    def test_high_price_stock_nvda_scenario(self):
        """测试高价股场景(如NVDA ~$900)
        
        验证修复Bug: 之前错误地将Unit等同于股数
        对于高价股，正确的计算应该给出合理的股数
        """
        analyzer = TurtleStrategyAnalyzer()
        
        # NVDA场景: 价格$900, N值约$12
        result = analyzer._calculate_position_size(
            account_equity=100000,
            n_value=12.0,
            dollar_per_point=1.0,
            current_price=900.0
        )
        
        # 风险单位 = 1000 / 12 = 83.33
        expected_units = 1000 / 12.0
        # 股数 = 83.33 * (12 / 900) ≈ 1.11股
        expected_shares = expected_units * (12.0 / 900.0)
        
        assert result['recommended_units'] == pytest.approx(expected_units, rel=0.01)
        assert result['position_size'] == pytest.approx(expected_shares, rel=0.01)
        # 修复Bug验证: position_size不应该等于recommended_units
        assert result['position_size'] != result['recommended_units']
    
    def test_low_price_stock_scenario(self):
        """测试低价股场景(如$5股票)
        
        低价股应该获得更多股数
        """
        analyzer = TurtleStrategyAnalyzer()
        
        result = analyzer._calculate_position_size(
            account_equity=100000,
            n_value=0.5,
            dollar_per_point=1.0,
            current_price=5.0
        )
        
        # 风险单位 = 1000 / 0.5 = 2000
        expected_units = 1000 / 0.5
        # 股数 = 2000 * (0.5 / 5) = 200股
        expected_shares = expected_units * (0.5 / 5.0)
        
        assert result['recommended_units'] == pytest.approx(expected_units, rel=0.01)
        assert result['position_size'] == pytest.approx(expected_shares, rel=0.01)
    
    def test_zero_n_value(self):
        """测试N值为零的情况"""
        analyzer = TurtleStrategyAnalyzer()
        
        result = analyzer._calculate_position_size(
            account_equity=100000,
            n_value=0,
            dollar_per_point=1.0,
            current_price=100.0
        )
        
        assert result['recommended_units'] == 0
        assert result['position_size'] == 0
    
    def test_no_current_price(self):
        """测试未提供当前价格时的回退行为"""
        analyzer = TurtleStrategyAnalyzer()
        
        result = analyzer._calculate_position_size(
            account_equity=100000,
            n_value=2.5,
            dollar_per_point=1.0,
            current_price=None
        )
        
        # 无价格时,position_size应等于recommended_units
        assert result['recommended_units'] == pytest.approx(400, rel=0.01)
        assert result['position_size'] == result['recommended_units']


class TestVolatilityPercentile:
    """波动率百分位测试"""
    
    def test_volatility_percentile(self):
        """测试波动率历史百分位计算"""
        strategy = TurtleStrategy()
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'Open': [100] * 100,
            'High': [105] * 100,
            'Low': [95] * 100,
            'Close': [100] * 100,
            'Volume': [1000000] * 100,
            'TR': [2] * 60 + [5] * 40,  # 后期波动增大
            'N': [2] * 60 + [5] * 40
        }, index=dates)
        
        percentile = strategy._calculate_volatility_percentile(data)
        
        # 最近的N=5较大，在N=[2]*60+[5]*40序列中
        # N=5排在第60-100位（100个中后40个）
        # percentile = 40/100 = 40%，表示排在后40%
        assert 30 <= percentile <= 50  # 应该在30-50%范围内
