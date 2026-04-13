"""
数据库会话与连接池管理模块
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # 连接前ping检查
    pool_size=10,            # 连接池大小
    max_overflow=20,         # 最大溢出连接数
    pool_recycle=3600,       # 连接回收时间(秒)
    echo=settings.DEBUG      # SQL日志输出
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建ORM基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    用于FastAPI的Depends注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库 - 创建所有表"""
    Base.metadata.create_all(bind=engine)
