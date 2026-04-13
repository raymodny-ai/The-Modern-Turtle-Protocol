#!/usr/bin/env python
"""分析API测试脚本"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from app.services.strategy import analyze_turtle_strategy

async def test_analyze():
    """测试完整分析流程"""
    print("=" * 60)
    print("🧪 开始API分析测试")
    print("=" * 60)
    
    # 生成测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    
    df = pd.DataFrame({
        'Open': prices + np.random.randn(100) * 0.5,
        'High': prices + abs(np.random.randn(100) * 2),
        'Low': prices - abs(np.random.randn(100) * 2),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # 执行分析
    result = analyze_turtle_strategy(
        df=df,
        account_equity=100000,
        dollar_per_point=1.0
    )
    
    print("\n📊 分析结果:")
    print("-" * 60)
    print(f"信号类型: {result['signal']}")
    print(f"信号原因: {result['signal_reason']}")
    print(f"当前价格: ${result['current_price']:.2f}")
    print(f"20日高点: ${result['channel_levels']['high_20_day']:.2f}")
    print(f"10日低点: ${result['channel_levels']['low_10_day']:.2f}")
    print(f"N值(ATR): ${result['volatility']['n_value']:.2f}")
    print(f"美元波动率: ${result['volatility']['dollar_volatility']:.2f}")
    print("-" * 60)
    print(f"建议单位: {result['position']['recommended_units']:.2f}")
    print(f"建议股数: {result['position']['position_size']:.0f}")
    print(f"风险金额: ${result['position']['risk_amount']:.2f}")
    print(f"最大持仓市值: ${result['position']['max_position_value']:.2f}")
    print("-" * 60)
    print(f"风险百分比: {result['risk_metrics']['risk_percentage']:.1f}%")
    print(f"风险金额: ${result['risk_metrics']['risk_amount']:.2f}")
    print("=" * 60)
    print("✅ 分析测试完成!")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_analyze())
