#!/usr/bin/env python
"""
数据库清理脚本
删除旧数据，保留最近N天的记录
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def cleanup_database(days_to_keep: int = 90):
    """
    清理数据库
    
    Args:
        days_to_keep: 保留最近多少天的数据
    """
    print(f"🧹 开始清理数据库，保留最近 {days_to_keep} 天的数据...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 清理旧的分析记录
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # 删除旧的非活跃信号
        result = conn.execute(
            text("""
                DELETE FROM analysis_records 
                WHERE is_active = false 
                AND analysis_time < :cutoff_date
            """),
            {"cutoff_date": cutoff_date}
        )
        print(f"   - 删除 {result.rowcount} 条旧分析记录")
        
        # 删除旧的已平仓持仓
        result = conn.execute(
            text("""
                DELETE FROM position_snapshots 
                WHERE is_closed = true 
                AND closed_at < :cutoff_date
            """),
            {"cutoff_date": cutoff_date}
        )
        print(f"   - 删除 {result.rowcount} 条已平仓记录")
        
        # 删除旧的已发送通知
        result = conn.execute(
            text("""
                DELETE FROM notification_logs 
                WHERE status = 'SENT' 
                AND sent_at < :cutoff_date
            """),
            {"cutoff_date": cutoff_date}
        )
        print(f"   - 删除 {result.rowcount} 条旧通知记录")
        
        # 清理过期的相关性数据
        result = conn.execute(
            text("""
                DELETE FROM market_correlations 
                WHERE valid_until IS NOT NULL 
                AND valid_until < :now
            """),
            {"now": datetime.now()}
        )
        print(f"   - 删除 {result.rowcount} 条过期相关性数据")
        
        conn.commit()
    
    print("✅ 数据库清理完成!")


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    cleanup_database(days)
