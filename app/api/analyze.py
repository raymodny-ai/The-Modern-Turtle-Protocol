"""
分析接口路由
现代海龟协议 - POST /api/v1/analyze
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.session import get_db
from app.schemas.trading import (
    AnalyzeRequest, 
    AnalyzeResponse, 
    SignalType,
    PriceData,
    ChannelLevels,
    VolatilityData,
    RiskMetrics,
    PositionRecommendation,
    SignalDetail
)
from app.services.fetch_data import get_market_data, DataSourceError
from app.services.strategy import analyze_turtle_strategy
from app.services.risk_manager import PortfolioRiskManager
from app.services.history import HistoryService
from app.services.notification import NotificationService
from app.database.models import PositionSnapshot

router = APIRouter(prefix="/analyze", tags=["分析"])


def _get_current_position(db: Session, ticker: str) -> dict:
    """
    从持仓表获取当前真实持仓
    
    修复: 真实持仓状态接入分析接口
    """
    position = db.query(PositionSnapshot).filter(
        PositionSnapshot.ticker == ticker.upper(),
        PositionSnapshot.is_closed == False
    ).first()
    
    if position:
        return {
            'has_position': True,
            'units': position.units,
            'shares': position.shares,
            'avg_entry_price': position.avg_entry_price,
            'position_type': position.position_type,
            'is_closed': position.is_closed,
            'opened_at': position.opened_at
        }
    else:
        return {
            'has_position': False,
            'units': 0,
            'shares': 0,
            'avg_entry_price': None,
            'position_type': None,
            'is_closed': True,
            'opened_at': None
        }


@router.post("", response_model=AnalyzeResponse)
async def analyze_ticker(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    执行海龟策略分析
    
    对指定资产执行完整的技术分析，包括:
    - 获取历史OHLCV数据
    - 计算N值/ATR
    - 生成交易信号(BUY/SELL/HOLD)
    - 计算头寸规模建议
    - 返回图表数据
    """
    try:
        # 1. 获取市场数据
        df = await get_market_data(
            ticker=request.ticker,
            period=request.period
        )
        
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail=f"无法获取 {request.ticker} 的市场数据"
            )
        
        # 2. 执行策略分析
        analysis_result = analyze_turtle_strategy(
            df=df,
            account_equity=request.account_equity,
            dollar_per_point=request.dollar_per_point
        )
        
        # 2.5 风险检查 - 修复: 将四重熔断接入主流程
        # 只有BUY信号才需要检查风险限制
        signal_type = analysis_result['signal']
        proposed_direction = "LONG" if signal_type == "BUY" else ("SHORT" if signal_type == "SELL" else None)
        risk_check_passed = True
        risk_blocked_reason = None
        
        if proposed_direction:
            risk_manager = PortfolioRiskManager(db)
            risk_result = risk_manager.check_risk_limits(
                ticker=request.ticker,
                proposed_direction=proposed_direction
            )
            risk_check_passed = risk_result.passed
            risk_blocked_reason = risk_result.blocked_reason
            
            # 如果风险检查未通过，调整信号状态
            if not risk_check_passed:
                analysis_result['signal'] = "HOLD"
                analysis_result['signal_reason'] = f"风险限制阻止交易: {risk_blocked_reason}"
        
        # 2.6 获取真实持仓状态 - 修复: 从持仓表获取
        current_position_data = _get_current_position(db, request.ticker)
        analysis_result['current_position_data'] = current_position_data
        
        # 3. 保存分析记录
        current_pos = analysis_result.get('current_position_data', {})
        history_service = HistoryService(db)
        record = history_service.save_analysis(
            ticker=request.ticker,
            signal=SignalType(analysis_result['signal']),
            current_price=analysis_result['current_price'],
            account_equity=request.account_equity,
            high_20_day=analysis_result['channel_levels'].get('high_20_day'),
            low_10_day=analysis_result['channel_levels'].get('low_10_day'),
            n_value=analysis_result['volatility'].get('n_value'),
            recommended_units=analysis_result['position'].get('recommended_units'),
            position_size=analysis_result['position'].get('position_size'),
            signal_reason=analysis_result['signal_reason'],
            dollar_volatility=analysis_result['volatility'].get('dollar_volatility'),
            dollar_per_point=request.dollar_per_point,
            risk_amount=analysis_result['position'].get('risk_amount'),
            current_positions=current_pos.get('units', 0)  # 修复: 写入真实持仓单位数
        )
        
        # 4. 发送通知(BUY/SELL信号)
        notification_service = NotificationService(db)
        await notification_service.send_signal_notification(
            ticker=request.ticker,
            signal=SignalType(analysis_result['signal']),
            signal_reason=analysis_result['signal_reason'],
            current_price=analysis_result['current_price'],
            n_value=analysis_result['volatility'].get('n_value', 0),
            recommended_units=analysis_result['position'].get('recommended_units', 0),
            position_size=analysis_result['position'].get('position_size', 0),
            analysis_id=record.id
        )
        
        # 5. 构建响应
        volatility = analysis_result['volatility']
        channel_levels = analysis_result['channel_levels']
        position = analysis_result['position']
        risk_metrics = analysis_result['risk_metrics']
        
        # 计算价格变动
        prev_close = analysis_result.get('previous_close')
        price_change = None
        price_change_pct = None
        if prev_close:
            price_change = analysis_result['current_price'] - prev_close
            price_change_pct = (price_change / prev_close) * 100
        
        return AnalyzeResponse(
            success=True,
            ticker=request.ticker,
            analysis_time=datetime.now(),
            current_price=analysis_result['current_price'],
            previous_close=prev_close,
            price_change=price_change,
            price_change_pct=round(price_change_pct, 2) if price_change_pct else None,
            signal=SignalType(analysis_result['signal']),
            signal_detail=SignalDetail(
                signal=SignalType(analysis_result['signal']),
                signal_reason=analysis_result['signal_reason'],
                price_action=analysis_result['signal_detail'].get('price_action', '')
            ),
            channel_levels=ChannelLevels(
                high_20_day=channel_levels.get('high_20_day'),
                low_10_day=channel_levels.get('low_10_day')
            ),
            volatility=VolatilityData(
                n_value=volatility.get('n_value'),
                dollar_volatility=volatility.get('dollar_volatility'),
                true_range_current=volatility.get('true_range_current')
            ),
            recommendation=PositionRecommendation(
                recommended_units=position.get('recommended_units', 0),
                position_size=position.get('position_size', 0),
                current_positions=current_pos.get('units', 0),  # 修复: 使用真实持仓
                can_add_position=position.get('can_add_position', False)
            ),
            risk_metrics=RiskMetrics(
                risk_percentage=risk_metrics.get('risk_percentage', 1.0),
                risk_amount=risk_metrics.get('risk_amount', 0),
                max_position_value=risk_metrics.get('max_position_value', 0)
            ),
            price_history=[
                PriceData(
                    date=p['date'],
                    open=p['open'],
                    high=p['high'],
                    low=p['low'],
                    close=p['close'],
                    volume=p['volume']
                )
                for p in analysis_result.get('price_history', [])
            ]
        )
        
    except DataSourceError as e:
        raise HTTPException(
            status_code=503,
            detail=f"数据源错误: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"分析过程发生错误: {str(e)}"
        )
