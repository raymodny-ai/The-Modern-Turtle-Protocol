"""
历史记录接口路由
现代海龟协议 - GET /api/v1/history
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.session import get_db
from app.schemas.trading import (
    HistoryQuery, 
    HistoryResponse, 
    HistoryRecord,
    SignalType
)
from app.services.history import HistoryService

router = APIRouter(prefix="/history", tags=["历史记录"])


@router.get("", response_model=HistoryResponse)
async def get_history(
    ticker: Optional[str] = Query(None, description="资产代码过滤"),
    signal: Optional[SignalType] = Query(None, description="信号类型过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(50, ge=1, le=500, description="返回记录数"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取历史分析记录
    
    支持:
    - 按资产代码过滤
    - 按信号类型过滤(BUY/SELL/HOLD)
    - 按日期范围过滤
    - 分页查询
    """
    try:
        history_service = HistoryService(db)
        
        query = HistoryQuery(
            ticker=ticker,
            signal=signal,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        records, total = history_service.get_history(query)
        
        return HistoryResponse(
            success=True,
            total=total,
            limit=limit,
            offset=offset,
            records=records
        )
        
    except Exception as e:
        return HistoryResponse(
            success=False,
            total=0,
            limit=limit,
            offset=offset,
            records=[]
        )


@router.get("/statistics")
async def get_statistics(
    ticker: Optional[str] = Query(None, description="资产代码"),
    days: int = Query(30, ge=1, le=365, description="统计周期(天)"),
    db: Session = Depends(get_db)
):
    """
    获取信号统计信息
    
    返回指定周期内的信号分布统计
    """
    try:
        history_service = HistoryService(db)
        stats = history_service.get_signal_statistics(
            ticker=ticker,
            days=days
        )
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
