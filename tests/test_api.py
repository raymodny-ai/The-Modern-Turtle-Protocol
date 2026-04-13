"""
API端点测试套件
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """健康检查端点测试"""
    
    def test_health_check(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestAnalyzeEndpoint:
    """分析端点测试"""
    
    def test_analyze_missing_ticker(self):
        """测试缺少ticker参数"""
        response = client.post(
            "/api/v1/analyze",
            json={"account_equity": 100000}
        )
        assert response.status_code == 422  # 验证错误
    
    def test_analyze_invalid_equity(self):
        """测试无效的账户资金"""
        response = client.post(
            "/api/v1/analyze",
            json={
                "ticker": "AAPL",
                "account_equity": -1000  # 负数无效
            }
        )
        assert response.status_code == 422


class TestHistoryEndpoint:
    """历史记录端点测试"""
    
    def test_get_history(self):
        """测试获取历史记录"""
        response = client.get("/api/v1/history")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
    
    def test_get_history_with_ticker_filter(self):
        """测试按ticker过滤"""
        response = client.get("/api/v1/history?ticker=AAPL")
        assert response.status_code == 200
    
    def test_get_history_pagination(self):
        """测试分页参数"""
        response = client.get("/api/v1/history?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestPositionsEndpoint:
    """持仓端点测试"""
    
    def test_get_positions(self):
        """测试获取持仓列表"""
        response = client.get("/api/v1/positions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_portfolio_summary(self):
        """测试投资组合摘要"""
        response = client.get("/api/v1/positions/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_positions" in data
        assert "limits" in data
