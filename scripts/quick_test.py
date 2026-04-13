#!/usr/bin/env python
"""快速测试脚本"""
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from app.services.strategy import TurtleStrategy

# 生成测试数据
dates = pd.date_range('2024-01-01', periods=60, freq='D')
np.random.seed(42)
prices = 100 + np.cumsum(np.random.randn(60) * 2)

data = pd.DataFrame({
    'Open': prices + np.random.randn(60) * 0.5,
    'High': prices + abs(np.random.randn(60) * 2),
    'Low': prices - abs(np.random.randn(60) * 2),
    'Close': prices,
    'Volume': np.random.randint(1000000, 10000000, 60)
}, index=dates)

strategy = TurtleStrategy()
data = strategy.calculate_indicators(data)
signal, reason, details = strategy.generate_signal(data)

print('=' * 50)
print('✅ 策略引擎测试成功!')
print('=' * 50)
print(f'信号: {signal}')
print(f'当前价: ${details["current_price"]:.2f}')
print(f'N值: ${details["n_value"]:.2f}')
print(f'20日高点: ${details["high_20_day"]:.2f}')
print(f'10日低点: ${details["low_10_day"]:.2f}')
print('=' * 50)

# 测试头寸计算
from app.services.strategy import TurtleStrategyAnalyzer
analyzer = TurtleStrategyAnalyzer()
result = analyzer._calculate_position_size(100000, details["n_value"], 1.0)
print(f'\n💰 头寸计算测试:')
print(f'建议单位: {result["recommended_units"]:.2f}')
print(f'风险金额: ${result["risk_amount"]:.2f}')
print(f'最大持仓市值: ${result["max_position_value"]:.2f}')
print('=' * 50)
