"""
pytest配置文件
"""

import pytest


def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        "test_ticker": "AAPL",
        "test_equity": 100000,
        "risk_percentage": 0.01
    }
