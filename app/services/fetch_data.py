"""
容灾型市场数据摄取模块
现代海龟协议 - 多源数据获取与故障转移
"""

import yfinance as yf
import httpx
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.core.config import settings


class DataSourceError(Exception):
    """数据源错误异常"""
    pass


class DataValidationError(Exception):
    """数据验证错误异常"""
    pass


class MarketDataFetcher:
    """
    多源容灾数据爬取模块
    
    支持数据源:
    - Yahoo Finance (主数据源)
    - Alpha Vantage (备用数据源)
    
    特性:
    - 自动故障转移
    - 数据完整性校验
    - 异步非阻塞请求
    """
    
    def __init__(self):
        self.primary_source = "yahoo_finance"
        self.fallback_source = "alpha_vantage"
        
    async def fetch_ohlcv(
        self, 
        ticker: str, 
        period: str = "1y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        获取OHLCV历史数据
        
        Args:
            ticker: 资产代码
            period: 数据周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo)
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            DataSourceError: 所有数据源都不可用
        """
        # 尝试主数据源 Yahoo Finance
        try:
            data = await self._fetch_from_yahoo(ticker, period, interval)
            if self._validate_data(data, ticker):
                return data
        except Exception as e:
            print(f"Yahoo Finance 获取失败: {e}")
        
        # 故障转移至 Alpha Vantage
        try:
            data = await self._fetch_from_alpha_vantage(ticker)
            if self._validate_data(data, ticker):
                return data
        except Exception as e:
            print(f"Alpha Vantage 获取失败: {e}")
        
        # 所有数据源都失败
        raise DataSourceError(
            f"无法从任何数据源获取 {ticker} 的市场数据。"
            f"请检查网络连接或数据源可用性。"
        )
    
    async def _fetch_from_yahoo(
        self, 
        ticker: str, 
        period: str,
        interval: str
    ) -> pd.DataFrame:
        """从Yahoo Finance获取数据
        
        修复: 改用get_running_loop()并在同步操作中添加超时控制
        """
        # 使用get_running_loop()替代已废弃的get_event_loop()
        loop = asyncio.get_running_loop()
        
        def _fetch():
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period=period, interval=interval)
                return df
            except Exception as e:
                raise DataSourceError(f"Yahoo Finance获取失败: {str(e)}")
        
        # 添加超时控制，避免高并发下线程池耗尽
        try:
            data = await asyncio.wait_for(
                loop.run_in_executor(None, _fetch),
                timeout=settings.DATA_REQUEST_TIMEOUT
            )
        except asyncio.TimeoutError:
            raise DataSourceError(f"Yahoo Finance获取超时: {ticker}")
        
        if data.empty:
            raise DataSourceError(f"Yahoo Finance返回空数据: {ticker}")
        
        return data
    
    async def _fetch_from_alpha_vantage(self, ticker: str) -> pd.DataFrame:
        """从Alpha Vantage获取数据"""
        if not settings.ALPHA_VANTAGE_API_KEY:
            raise DataSourceError("Alpha Vantage API Key未配置")
        
        async with httpx.AsyncClient(timeout=settings.DATA_REQUEST_TIMEOUT) as client:
            # 优先使用TIME_SERIES_DAILY_ADJUSTED
            response = await client.get(
                settings.ALPHA_VANTAGE_BASE_URL,
                params={
                    "function": "TIME_SERIES_DAILY_ADJUSTED",
                    "symbol": ticker,
                    "apikey": settings.ALPHA_VANTAGE_API_KEY,
                    "outputsize": "full"
                }
            )
            
            if response.status_code != 200:
                raise DataSourceError(f"Alpha Vantage HTTP错误: {response.status_code}")
            
            data = response.json()
            
            if "Error Message" in data:
                raise DataSourceError(f"Alpha Vantage API错误: {data['Error Message']}")
            
            if "Note" in data:
                raise DataSourceError("Alpha Vantage API请求频率超限")
            
            # 解析数据
            time_series_key = "Time Series (Daily)"
            if time_series_key not in data:
                raise DataSourceError("Alpha Vantage返回数据格式异常")
            
            records = []
            for date_str, values in data[time_series_key].items():
                records.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': float(values['6. volume'])
                })
            
            df = pd.DataFrame(records)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            # 只保留最近一年的数据
            one_year_ago = datetime.now() - timedelta(days=365)
            df = df[df.index >= one_year_ago]
            
            return df
    
    def _validate_data(self, data: pd.DataFrame, ticker: str) -> bool:
        """
        验证数据完整性
        
        检查项:
        1. 数据不为空
        2. 包含必要的OHLCV列
        3. 没有严重的缺失值
        4. 价格数据合理(无负数、零值)
        """
        if data.empty:
            return False
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in data.columns:
                return False
        
        # 检查缺失值比例
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_ratio > 0.05:  # 超过5%缺失值
            raise DataValidationError(f"数据缺失率过高: {missing_ratio:.2%}")
        
        # 检查价格合理性
        if (data['Close'] <= 0).any() or (data['High'] <= 0).any() or (data['Low'] <= 0).any():
            raise DataValidationError("价格数据包含非正值")
        
        # 检查高低价关系
        invalid = (data['High'] < data['Low']).any() or \
                  (data['Close'] > data['High']).any() or \
                  (data['Close'] < data['Low']).any()
        if invalid:
            raise DataValidationError("价格数据违反OHLC逻辑关系")
        
        return True
    
    async def get_current_price(self, ticker: str) -> float:
        """获取当前实时价格"""
        try:
            data = await self._fetch_from_yahoo(ticker, "5d", "1d")
            return float(data['Close'].iloc[-1])
        except Exception:
            # 备用方案
            data = await self._fetch_from_alpha_vantage(ticker)
            return float(data['Close'].iloc[-1])


# 全局数据获取器实例
market_data_fetcher = MarketDataFetcher()


async def get_market_data(
    ticker: str, 
    period: str = "1y",
    interval: str = "1d"
) -> pd.DataFrame:
    """获取市场数据的便捷函数"""
    return await market_data_fetcher.fetch_ohlcv(ticker, period, interval)
