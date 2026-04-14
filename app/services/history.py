"""
历史记录持久化模块
现代海龟协议 - 策略执行历史追踪
"""

from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.database.models import AnalysisRecord, SignalType as DBSignalType
from app.schemas.trading import HistoryRecord, HistoryQuery, SignalType


class HistoryService:
    """历史记录服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_analysis(
        self,
        ticker: str,
        signal: SignalType,
        current_price: float,
        account_equity: float,
        high_20_day: Optional[float] = None,
        low_10_day: Optional[float] = None,
        n_value: Optional[float] = None,
        recommended_units: Optional[float] = None,
        position_size: Optional[float] = None,
        signal_reason: Optional[str] = None,
        dollar_volatility: Optional[float] = None,
        dollar_per_point: float = 1.0,
        risk_amount: Optional[float] = None,  # 修复: 添加risk_amount参数
        error_message: Optional[str] = None
    ) -> AnalysisRecord:
        """
        保存分析记录
        
        修复: risk_amount字段写入数据库
        """
        record = AnalysisRecord(
            ticker=ticker.upper(),
            signal=DBSignalType(signal.value),
            current_price=current_price,
            account_equity=account_equity,
            high_20_day=high_20_day,
            low_10_day=low_10_day,
            n_value=n_value,
            recommended_units=recommended_units,
            position_size=position_size,
            signal_reason=signal_reason,
            dollar_volatility=dollar_volatility,
            dollar_per_point=dollar_per_point,
            risk_amount=risk_amount,  # 修复: 保存risk_amount
            error_message=error_message,
            is_active=signal != SignalType.HOLD  # HOLD信号不标记为活跃
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def get_history(
        self,
        query: HistoryQuery
    ) -> Tuple[List[HistoryRecord], int]:
        """
        获取历史记录
        
        Args:
            query: 查询条件
            
        Returns:
            (记录列表, 总数)
        """
        # 构建查询条件
        filters = []
        
        if query.ticker:
            filters.append(AnalysisRecord.ticker == query.ticker.upper())
        
        if query.signal:
            filters.append(AnalysisRecord.signal == DBSignalType(query.signal.value))
        
        if query.start_date:
            filters.append(AnalysisRecord.analysis_time >= query.start_date)
        
        if query.end_date:
            filters.append(AnalysisRecord.analysis_time <= query.end_date)
        
        # 构建查询
        db_query = self.db.query(AnalysisRecord)
        
        if filters:
            db_query = db_query.filter(and_(*filters))
        
        # 获取总数
        total = db_query.count()
        
        # 应用分页和排序
        records = (
            db_query
            .order_by(desc(AnalysisRecord.analysis_time))
            .offset(query.offset)
            .limit(query.limit)
            .all()
        )
        
        # 转换为响应模型
        history_records = [
            HistoryRecord(
                id=r.id,
                ticker=r.ticker,
                analysis_time=r.analysis_time,
                current_price=r.current_price,
                signal=SignalType(r.signal.value),
                signal_reason=r.signal_reason,
                high_20_day=r.high_20_day,
                low_10_day=r.low_10_day,
                n_value=r.n_value,
                recommended_units=r.recommended_units,
                position_size=r.position_size,
                account_equity=r.account_equity,
                is_active=r.is_active
            )
            for r in records
        ]
        
        return history_records, total
    
    def get_latest_analysis(self, ticker: str) -> Optional[AnalysisRecord]:
        """获取某资产最新分析记录"""
        return (
            self.db.query(AnalysisRecord)
            .filter(AnalysisRecord.ticker == ticker.upper())
            .order_by(desc(AnalysisRecord.analysis_time))
            .first()
        )
    
    def get_signal_statistics(
        self,
        ticker: Optional[str] = None,
        days: int = 30
    ) -> dict:
        """获取信号统计"""
        from datetime import timedelta
        
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AnalysisRecord).filter(
            AnalysisRecord.analysis_time >= start_date
        )
        
        if ticker:
            query = query.filter(AnalysisRecord.ticker == ticker.upper())
        
        records = query.all()
        
        # 统计各信号数量
        signals = {}
        for record in records:
            sig = record.signal.value
            signals[sig] = signals.get(sig, 0) + 1
        
        return {
            'total': len(records),
            'signals': signals,
            'period_days': days,
            'ticker': ticker,
            'start_date': start_date,
            'end_date': datetime.now()
        }
    
    def deactivate_old_signals(self, ticker: str, except_id: int = None):
        """停用旧信号"""
        query = self.db.query(AnalysisRecord).filter(
            AnalysisRecord.ticker == ticker.upper(),
            AnalysisRecord.is_active == True
        )
        
        if except_id:
            query = query.filter(AnalysisRecord.id != except_id)
        
        query.update({'is_active': False})
        self.db.commit()
