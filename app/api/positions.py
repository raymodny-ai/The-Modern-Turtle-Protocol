"""
持仓管理接口路由
现代海龟协议 - 持仓相关API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database.session import get_db
from app.database.models import PositionSnapshot
from app.schemas.trading import PositionAddRequest, PositionResponse
from app.services.risk_manager import PortfolioRiskManager

router = APIRouter(prefix="/positions", tags=["持仓管理"])


@router.get("", response_model=List[PositionResponse])
async def get_positions(
    ticker: str = None,
    include_closed: bool = False,
    db: Session = Depends(get_db)
):
    """获取当前持仓列表"""
    query = db.query(PositionSnapshot)
    
    if ticker:
        query = query.filter(PositionSnapshot.ticker == ticker.upper())
    
    if not include_closed:
        query = query.filter(PositionSnapshot.is_closed == False)
    
    positions = query.order_by(PositionSnapshot.opened_at.desc()).all()
    
    return [
        PositionResponse(
            id=p.id,
            ticker=p.ticker,
            position_type=p.position_type,
            units=p.units,
            shares=p.shares,
            avg_entry_price=p.avg_entry_price,
            n_value_at_entry=p.n_value_at_entry,
            stop_loss_price=p.stop_loss_price,
            opened_at=p.opened_at,
            is_closed=p.is_closed
        )
        for p in positions
    ]


@router.post("")
async def add_position(
    request: PositionAddRequest,
    db: Session = Depends(get_db)
):
    """添加新持仓"""
    try:
        # 风险检查
        risk_manager = PortfolioRiskManager(db)
        risk_result = risk_manager.check_risk_limits(
            ticker=request.ticker,
            proposed_direction=request.position_type
        )
        
        if not risk_result.passed:
            raise HTTPException(
                status_code=400,
                detail=risk_result.blocked_reason
            )
        
        # 计算止损价格
        if request.position_type == "LONG":
            stop_loss = request.entry_price - (2 * request.n_value)
        else:
            stop_loss = request.entry_price + (2 * request.n_value)
        
        # 创建持仓记录
        position = PositionSnapshot(
            ticker=request.ticker.upper(),
            position_type=request.position_type,
            units=1,
            shares=request.shares,
            avg_entry_price=request.entry_price,
            n_value_at_entry=request.n_value,
            stop_loss_price=round(stop_loss, 2),
            risk_per_unit=request.n_value * request.shares,
            opened_at=datetime.now()
        )
        
        db.add(position)
        db.commit()
        db.refresh(position)
        
        return {
            "success": True,
            "message": f"成功添加 {request.ticker} 持仓",
            "position_id": position.id,
            "stop_loss": stop_loss
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{position_id}/close")
async def close_position(
    position_id: int,
    exit_price: float,
    db: Session = Depends(get_db)
):
    """平仓"""
    position = db.query(PositionSnapshot).filter(
        PositionSnapshot.id == position_id
    ).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")
    
    if position.is_closed:
        raise HTTPException(status_code=400, detail="持仓已平仓")
    
    # 更新持仓状态
    position.is_closed = True
    position.closed_at = datetime.now()
    
    # 计算盈亏
    if position.position_type == "LONG":
        pnl = (exit_price - position.avg_entry_price) * position.shares
    else:
        pnl = (position.avg_entry_price - exit_price) * position.shares
    
    db.commit()
    
    return {
        "success": True,
        "position_id": position_id,
        "exit_price": exit_price,
        "pnl": round(pnl, 2)
    }


@router.get("/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """获取投资组合摘要"""
    risk_manager = PortfolioRiskManager(db)
    return risk_manager.get_portfolio_summary()
