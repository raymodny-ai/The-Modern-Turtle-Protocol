#!/usr/bin/env python
"""
数据库初始化脚本
创建数据库表结构
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import engine, Base
from app.database.models import AnalysisRecord, PositionSnapshot, MarketCorrelation, NotificationLog


def init_database():
    """初始化数据库表"""
    print("📦 正在创建数据库表...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功!")
        
        # 列出创建的表
        print("\n📋 创建的表:")
        for table_name in Base.metadata.tables.keys():
            print(f"   - {table_name}")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)


def drop_tables():
    """删除所有表（谨慎使用）"""
    print("⚠️  警告: 即将删除所有数据库表...")
    confirm = input("确认删除? (输入 'yes' 确认): ")
    
    if confirm.lower() == 'yes':
        Base.metadata.drop_all(bind=engine)
        print("✅ 所有表已删除")
    else:
        print("❌ 操作已取消")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_tables()
    else:
        init_database()
