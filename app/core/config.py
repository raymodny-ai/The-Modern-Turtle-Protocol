"""
核心配置模块
现代海龟协议量化交易系统 - 环境配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用全局配置类"""
    
    # ============================================
    # 应用基本信息
    # ============================================
    APP_NAME: str = "现代海龟协议量化交易系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============================================
    # 数据库配置
    # ============================================
    DATABASE_URL: str = "sqlite:///./turtle_trading.db"
    
    # ============================================
    # API配置
    # ============================================
    API_V1_PREFIX: str = "/api/v1"
    
    # ============================================
    # 数据源配置
    # ============================================
    # Yahoo Finance (主数据源)
    YAHOO_FINANCE_ENABLED: bool = True
    
    # Alpha Vantage (备用数据源)
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    
    # 数据请求配置
    DATA_REQUEST_TIMEOUT: int = 30  # 秒
    MAX_RETRY_ATTEMPTS: int = 3
    
    # ============================================
    # 交易策略参数 (海龟协议核心参数)
    # ============================================
    # 突破周期参数
    ENTRY_PERIOD: int = 20   # 20日最高价突破
    EXIT_PERIOD: int = 10    # 10日最低价跌破
    
    # ATR/N值参数
    ATR_PERIOD: int = 20    # 20日ATR平滑周期
    
    # 风险管理参数
    RISK_PERCENTAGE: float = 0.01  # 每笔交易1%风险
    
    # 头寸限制参数
    SINGLE_MARKET_LIMIT: int = 4      # 单一市场最多4个单位
    CLOSELY_CORRELATED_LIMIT: int = 6  # 高关联市场最多6个单位
    LOOSELY_CORRELATED_LIMIT: int = 10 # 弱关联市场最多10个单位
    SINGLE_DIRECTION_LIMIT: int = 12   # 单向总敞口最多12个单位
    
    # ============================================
    # 通知系统配置
    # ============================================
    NOTIFICATION_ENABLED: bool = True
    
    # SMTP配置
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TO: list[str] = []
    
    # Webhook配置
    WEBHOOK_URL: Optional[str] = None
    
    # ============================================
    # 安全配置
    # ============================================
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 全局配置实例
settings = get_settings()
