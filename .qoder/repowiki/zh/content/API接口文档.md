# API接口文档

<cite>
**本文档引用的文件**
- [app/main.py](file://app/main.py)
- [app/api/analyze.py](file://app/api/analyze.py)
- [app/api/history.py](file://app/api/history.py)
- [app/api/positions.py](file://app/api/positions.py)
- [app/core/security.py](file://app/core/security.py)
- [app/services/backtest.py](file://app/services/backtest.py)
- [app/schemas/trading.py](file://app/schemas/trading.py)
- [app/services/history.py](file://app/services/history.py)
- [app/services/risk_manager.py](file://app/services/risk_manager.py)
- [app/database/models.py](file://app/database/models.py)
- [app/core/config.py](file://app/core/config.py)
- [requirements.txt](file://requirements.txt)
- [scripts/test_analyze.py](file://scripts/test_analyze.py)
- [scripts/quick_test.py](file://scripts/quick_test.py)
- [tests/test_api.py](file://tests/test_api.py)
</cite>

## 更新摘要
**变更内容**
- 新增完整的安全认证体系，包括JWT认证、RBAC权限控制和审计日志
- 新增回测框架适配器，支持QSTrader和PyAlgoTrade专业回测平台
- 新增测试API端点，提供开发环境下的认证测试功能
- 增强现有API的安全性和权限控制机制
- 新增蒙特卡洛模拟和风险评估功能

## 目录
1. [简介](#简介)
2. [系统架构](#系统架构)
3. [API端点概览](#api端点概览)
4. [核心API接口](#核心api接口)
5. [安全认证体系](#安全认证体系)
6. [回测框架集成](#回测框架集成)
7. [测试API端点](#测试api端点)
8. [数据模型规范](#数据模型规范)
9. [错误处理与状态码](#错误处理与状态码)
10. [性能优化建议](#性能优化建议)
11. [OpenAPI规范](#openapispec)
12. [客户端实现指南](#客户端实现指南)
13. [部署与监控](#部署与监控)

## 简介

《现代海龟协议》是一个基于Python与微服务架构的自动化量化交易系统。该系统实现了经典海龟交易法则的数字化转型，通过严格的系统性风险管理框架和波动率导向的资金分配机制，为量化交易员提供了一套完整的自动化交易解决方案。

系统采用FastAPI作为核心Web框架，结合PostgreSQL数据库和先进的量化计算库，实现了从数据获取、策略分析到历史记录管理的完整交易生命周期。本文档详细描述了系统的RESTful API接口规范，涵盖策略分析、历史记录查询、持仓管理、安全认证和回测框架集成等核心功能。

**更新** 新增了完整的安全认证体系和回测框架集成，增强了系统的专业性和实用性。

## 系统架构

系统采用分层架构设计，确保各层职责清晰、耦合度低：

```mermaid
graph TD
subgraph "客户端层"
WEB[Web浏览器]
MOBILE[移动应用]
SCRIPTS[自动化脚本]
API_CLIENTS[第三方API客户端]
TEST_TOOLS[测试工具]
end
subgraph "API网关层"
ROUTER[FastAPI路由]
AUTH[认证中间件]
VALIDATION[数据验证]
CORS[CORS中间件]
SECURITY_AUDIT[安全审计]
ENDPOINT_HEALTH[端点健康检查]
end
subgraph "业务逻辑层"
ANALYZE_SERVICE[策略分析服务]
HISTORY_SERVICE[历史记录服务]
POSITION_SERVICE[持仓管理服务]
RISK_MANAGER[风险管理系统]
NOTIFICATION_SERVICE[通知服务]
BACKTEST_SERVICE[回测服务]
SECURITY_SERVICE[安全服务]
end
subgraph "数据访问层"
DATABASE[(PostgreSQL)]
REDIS_CACHE[Redis缓存]
end
subgraph "外部服务"
DATA_SOURCES[数据源]
ALPHA_VANTAGE[Alpha Vantage]
YAHOO_FINANCE[Yahoo Finance]
NOTIFICATION[邮件/Webhook]
end
WEB --> ROUTER
MOBILE --> ROUTER
SCRIPTS --> ROUTER
API_CLIENTS --> ROUTER
TEST_TOOLS --> ROUTER
ROUTER --> AUTH
AUTH --> VALIDATION
VALIDATION --> SECURITY_AUDIT
SECURITY_AUDIT --> CORS
CORS --> ENDPOINT_HEALTH
ENDPOINT_HEALTH --> ANALYZE_SERVICE
ENDPOINT_HEALTH --> HISTORY_SERVICE
ENDPOINT_HEALTH --> POSITION_SERVICE
ANALYZE_SERVICE --> HISTORY_SERVICE
ANALYZE_SERVICE --> NOTIFICATION_SERVICE
POSITION_SERVICE --> RISK_MANAGER
RISK_MANAGER --> DATABASE
HISTORY_SERVICE --> DATABASE
ANALYZE_SERVICE --> DATABASE
DATABASE --> DATA_SOURCES
DATA_SOURCES --> YAHOO_FINANCE
DATA_SOURCES --> ALPHA_VANTAGE
NOTIFICATION_SERVICE --> NOTIFICATION
```

**图表来源**
- [app/main.py:32-89](file://app/main.py#L32-L89)
- [app/core/config.py:11-99](file://app/core/config.py#L11-L99)

## API端点概览

系统提供以下主要API端点：

### 核心分析接口
- **POST /api/v1/analyze** - 策略分析接口
- **GET /api/v1/history** - 历史记录查询接口
- **GET /api/v1/history/statistics** - 信号统计查询接口

### 持仓管理接口
- **GET /api/v1/positions** - 获取当前持仓列表
- **POST /api/v1/positions** - 添加新持仓
- **POST /api/v1/positions/{position_id}/close** - 平仓
- **GET /api/v1/positions/summary** - 获取投资组合摘要

### 系统接口
- **GET /health** - 系统健康检查
- **GET /api/v1/health** - API健康状态

### 安全认证接口
- **POST /auth/login** - 用户登录
- **GET /auth/me** - 获取当前用户信息
- **GET /auth/test-token** - 获取测试Token
- **GET /audit/logs** - 获取安全审计日志

### 回测框架接口
- **POST /api/v1/backtest/run** - 运行回测
- **GET /api/v1/backtest/frameworks** - 获取可用回测框架

**章节来源**
- [app/main.py:85-89](file://app/main.py#L85-L89)
- [app/api/analyze.py:27](file://app/api/analyze.py#L27)
- [app/api/history.py:20](file://app/api/history.py#L20)
- [app/api/positions.py:16](file://app/api/positions.py#L16)
- [app/main.py:124-196](file://app/main.py#L124-L196)

## 核心API接口

### 策略分析接口 (POST /api/v1/analyze)

#### 接口概述

策略分析接口是系统的核心功能端点，负责接收资产分析请求并返回详细的交易信号和风险参数。

#### 请求规范

| 属性 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| ticker | 资产代码 | string | 是 | - | 支持股票、外汇、期货代码 |
| account_equity | 账户净资产 | number | 是 | > 0 | 美元金额 |
| period | 数据周期 | string | 否 | "1y" | 支持1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max |
| dollar_per_point | 每点美元价值 | number | 否 | 1.0 | 股票默认1.0，外汇/期货需配置 |

**请求示例**
```json
{
  "ticker": "AAPL",
  "account_equity": 100000,
  "period": "1y",
  "dollar_per_point": 1.0
}
```

#### 响应规范

| 字段 | 描述 | 类型 | 示例值 |
|------|------|------|--------|
| success | 分析是否成功 | boolean | true |
| ticker | 资产代码 | string | "AAPL" |
| analysis_time | 分析时间 | datetime | "2024-01-15T10:30:00Z" |
| current_price | 当前收盘价 | number | 150.25 |
| previous_close | 前一日收盘价 | number | 148.75 |
| price_change | 价格变动 | number | 1.50 |
| price_change_pct | 价格变动百分比 | number | 1.01 |
| signal | 交易信号 | enum | "BUY" |
| signal_detail | 信号详情 | object | - |
| channel_levels | 通道水平 | object | - |
| volatility | 波动率数据 | object | - |
| recommendation | 持仓建议 | object | - |
| risk_metrics | 风险指标 | object | - |
| price_history | 历史价格数据 | array | - |
| error | 错误信息 | string | null |

**响应示例**
```json
{
  "success": true,
  "ticker": "AAPL",
  "analysis_time": "2024-01-15T10:30:00Z",
  "current_price": 150.25,
  "previous_close": 148.75,
  "price_change": 1.50,
  "price_change_pct": 1.01,
  "signal": "BUY",
  "signal_detail": {
    "signal": "BUY",
    "signal_reason": "价格突破20日最高价，趋势向上",
    "price_action": "突破买入"
  },
  "channel_levels": {
    "high_20_day": 145.20,
    "low_10_day": 142.10
  },
  "volatility": {
    "n_value": 2.45,
    "dollar_volatility": 245.00,
    "true_range_current": 2.30
  },
  "recommendation": {
    "recommended_units": 3.0,
    "position_size": 57.0,
    "current_positions": 0,
    "can_add_position": true
  },
  "risk_metrics": {
    "risk_percentage": 1.0,
    "risk_amount": 1000.00,
    "max_position_value": 100000.00
  },
  "price_history": [
    {
      "date": "2024-01-15T00:00:00Z",
      "open": 148.50,
      "high": 150.25,
      "low": 147.80,
      "close": 150.25,
      "volume": 1000000
    }
  ]
}
```

#### 处理流程

```mermaid
sequenceDiagram
participant Client as 客户端
participant API as API网关
participant Auth as 认证服务
participant Strategy as 策略服务
participant Data as 数据源
participant DB as 数据库
participant Notification as 通知服务
Client->>API : POST /api/v1/analyze
API->>Auth : 验证JWT令牌
Auth-->>API : 返回用户信息
API->>Strategy : 验证请求参数
Strategy->>Data : 获取市场数据
Data-->>Strategy : 返回OHLCV数据
Strategy->>Strategy : 计算技术指标
Strategy->>Strategy : 生成交易信号
Strategy->>DB : 保存分析记录
DB-->>Strategy : 确认保存
Strategy->>Notification : 发送信号通知
Notification-->>Strategy : 通知发送确认
Strategy-->>API : 返回分析结果
API-->>Client : 返回JSON响应
```

**图表来源**
- [app/api/analyze.py:30-168](file://app/api/analyze.py#L30-L168)

#### 错误处理

| 错误代码 | 描述 | 处理方式 |
|----------|------|----------|
| 400 | 参数验证失败或数据源错误 | 返回详细错误信息 |
| 401 | 未认证或认证失败 | 返回未授权错误 |
| 403 | 权限不足 | 返回权限拒绝错误 |
| 404 | 资产代码无效 | 提示资产不存在 |
| 500 | 服务器内部错误 | 记录日志并返回通用错误 |
| 503 | 数据源不可用 | 返回重试建议 |

**章节来源**
- [app/api/analyze.py:156-167](file://app/api/analyze.py#L156-L167)

### 历史记录查询接口 (GET /api/v1/history)

#### 接口概述

历史记录查询接口提供对系统分析历史的分页查询功能，支持多种筛选条件和排序选项。

#### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| ticker | 资产代码 | string | 否 | - | 支持模糊匹配 |
| signal | 交易信号 | enum | 否 | - | BUY/SELL/HOLD |
| start_date | 开始日期 | datetime | 否 | - | ISO 8601格式 |
| end_date | 结束日期 | datetime | 否 | - | ISO 8601格式 |
| limit | 每页记录数 | integer | 否 | 50 | 1-500之间 |
| offset | 偏移量 | integer | 否 | 0 | 分页偏移 |
| sort_by | 排序字段 | string | 否 | analysis_time | 支持id,analysis_time,ticker |
| order | 排序方向 | string | 否 | desc | asc/desc |

#### 响应结构

**响应示例**
```json
{
  "success": true,
  "total": 1234,
  "limit": 50,
  "offset": 0,
  "records": [
    {
      "id": 1,
      "ticker": "AAPL",
      "analysis_time": "2024-01-15T10:30:00Z",
      "current_price": 150.25,
      "signal": "BUY",
      "signal_reason": "价格突破20日最高价",
      "high_20_day": 145.20,
      "low_10_day": 142.10,
      "n_value": 2.45,
      "recommended_units": 3.0,
      "position_size": 57.0,
      "account_equity": 100000.0,
      "is_active": true
    }
  ]
}
```

#### 性能优化

```mermaid
flowchart TD
Request[请求到达] --> Validate[参数验证]
Validate --> BuildQuery[构建查询条件]
BuildQuery --> ApplyIndex[应用索引优化]
ApplyIndex --> ExecuteQuery[执行数据库查询]
ExecuteQuery --> Paginate[分页处理]
Paginate --> Transform[数据转换]
Transform --> Response[返回响应]
subgraph "数据库索引优化"
TickerIdx[ticker索引]
TimeIdx[analysis_time索引]
SignalIdx[signal索引]
ActiveIdx[is_active索引]
end
ApplyIndex --> TickerIdx
ApplyIndex --> TimeIdx
ApplyIndex --> SignalIdx
ApplyIndex --> ActiveIdx
```

**图表来源**
- [app/database/models.py:61-65](file://app/database/models.py#L61-L65)

**章节来源**
- [app/api/history.py:23-71](file://app/api/history.py#L23-L71)
- [app/database/models.py:19-68](file://app/database/models.py#L19-L68)

### 信号统计查询接口 (GET /api/v1/history/statistics)

#### 接口概述

信号统计查询接口提供指定周期内信号分布的统计信息。

#### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| ticker | 资产代码 | string | 否 | - | 可选，按资产过滤 |
| days | 统计周期 | integer | 否 | 30 | 1-365之间 |

#### 响应结构

**响应示例**
```json
{
  "success": true,
  "total": 150,
  "signals": {
    "BUY": 80,
    "SELL": 45,
    "HOLD": 25
  },
  "period_days": 30,
  "ticker": "AAPL",
  "start_date": "2024-01-15T10:30:00Z",
  "end_date": "2024-02-15T10:30:00Z"
}
```

**章节来源**
- [app/api/history.py:74-102](file://app/api/history.py#L74-L102)

### 持仓管理接口

#### 获取持仓列表 (GET /api/v1/positions)

##### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| ticker | 资产代码 | string | 否 | - | 可选过滤条件 |
| include_closed | 包含已平仓 | boolean | 否 | false | 是否包含已平仓持仓 |

##### 响应结构

**响应示例**
```json
[
  {
    "id": 1,
    "ticker": "AAPL",
    "position_type": "LONG",
    "units": 1,
    "shares": 57.0,
    "avg_entry_price": 145.20,
    "n_value_at_entry": 2.45,
    "stop_loss_price": 140.30,
    "opened_at": "2024-01-15T10:30:00Z",
    "is_closed": false,
    "unrealized_pnl": 140.00,
    "current_price": 150.25
  }
]
```

#### 添加新持仓 (POST /api/v1/positions)

##### 请求规范

| 属性 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| ticker | 资产代码 | string | 是 | - | - |
| position_type | 持仓类型 | enum | 是 | - | "LONG" 或 "SHORT" |
| shares | 持仓股数 | number | 是 | > 0 | - |
| entry_price | 入场价格 | number | 是 | > 0 | - |
| n_value | 入场时N值 | number | 是 | > 0 | - |

##### 响应结构

**响应示例**
```json
{
  "success": true,
  "message": "成功添加 AAPL 持仓",
  "position_id": 1,
  "stop_loss": 140.30
}
```

#### 平仓 (POST /api/v1/positions/{position_id}/close)

##### 路径参数

| 参数名 | 描述 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| position_id | 持仓ID | integer | 是 | - |

##### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| exit_price | 出场价格 | number | 是 | - |

##### 响应结构

**响应示例**
```json
{
  "success": true,
  "position_id": 1,
  "exit_price": 150.25,
  "pnl": 140.00
}
```

#### 投资组合摘要 (GET /api/v1/positions/summary)

##### 响应结构

**响应示例**
```json
{
  "total_positions": 5,
  "total_exposure": 8,
  "long_units": 6,
  "short_units": 2,
  "net_exposure": 4,
  "by_ticker": {
    "AAPL": {
      "units": 3,
      "positions": [1, 2]
    },
    "MSFT": {
      "units": 2,
      "positions": [3]
    }
  },
  "limits": {
    "single_market": 4,
    "high_correlation": 6,
    "low_correlation": 10,
    "single_direction": 12
  },
  "utilization": {
    "long": 50.0,
    "short": 16.67
  }
}
```

**章节来源**
- [app/api/positions.py:19-152](file://app/api/positions.py#L19-L152)

## 安全认证体系

### 认证接口

#### 用户登录 (POST /auth/login)

##### 请求规范

| 参数名 | 描述 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| username | 用户名 | string | 是 | - |
| password | 密码 | string | 是 | - |

##### 响应结构

**响应示例**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "trader"
}
```

#### 获取当前用户信息 (GET /auth/me)

##### 响应结构

**响应示例**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "permissions": ["analyze:read", "analyze:write", "history:read"]
}
```

#### 获取测试Token (GET /auth/test-token)

##### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| user_id | 用户ID | integer | 否 | 默认1 |

##### 响应结构

**响应示例**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "note": "仅用于开发测试"
}
```

#### 获取安全审计日志 (GET /audit/logs)

##### 查询参数

| 参数名 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| limit | 日志数量 | integer | 否 | 100 | - |

##### 响应结构

**响应示例**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "user_id": 1,
      "username": "admin",
      "endpoint": "/api/v1/analyze",
      "method": "POST",
      "ip_address": "127.0.0.1",
      "status_code": 200,
      "user_agent": "Mozilla/5.0...",
      "event_type": "ACCESS"
    }
  ]
}
```

### RBAC权限控制

系统采用基于角色的权限控制(RBAC)，支持以下角色和权限：

| 角色 | 权限范围 | 可访问端点 |
|------|----------|------------|
| ADMIN | 完全权限 | 所有端点 |
| TRADER | 交易相关 | 分析、历史、持仓管理 |
| ANALYST | 只读分析 | 分析、历史查询 |
| VIEWER | 仅查看 | 分析查看 |

##### 权限映射

```mermaid
graph TD
ADMIN[管理员] --> FULL_ACCESS[完全访问]
TRADER[交易员] --> ANALYZE_ACCESS[分析访问]
TRADER --> HISTORY_ACCESS[历史访问]
TRADER --> POSITIONS_ACCESS[持仓管理]
ANALYST[分析师] --> READ_ANALYZE[只读分析]
ANALYST --> READ_HISTORY[只读历史]
VIEWER[查看者] --> READ_ANALYZE
VIEWER --> READ_POSITIONS[只读持仓]
```

**图表来源**
- [app/core/security.py:238-261](file://app/core/security.py#L238-L261)

### 安全审计

系统提供完整的安全审计功能，记录所有重要操作：

- **访问日志**: 记录用户访问API端点
- **认证失败**: 记录登录失败和权限拒绝
- **操作审计**: 记录关键业务操作
- **IP追踪**: 跟踪用户IP地址和User-Agent

**章节来源**
- [app/main.py:124-196](file://app/main.py#L124-L196)
- [app/core/security.py:230-473](file://app/core/security.py#L230-L473)

## 回测框架集成

### 回测框架适配器

系统支持与专业回测框架的集成，提供统一的回测接口：

#### 支持的回测框架

| 框架名称 | 特性 | 依赖包 |
|----------|------|--------|
| QSTrader | 专业量化交易框架 | qstrader |
| PyAlgoTrade | 事件驱动架构 | pyalgotrade |
| Custom | 自定义回测框架 | 内置 |

#### 回测结果指标

| 指标名称 | 描述 | 计算公式 |
|----------|------|----------|
| 总收益率 | 整个回测期间的总收益 | (最终资金-初始资金)/初始资金 |
| 夏普比率 | 风险调整后的收益 | 平均收益/std偏差×√252 |
| 最大回撤 | 最大资金回撤幅度 | max((资金-运行最大值)/运行最大值) |
| 胜率 | 盈利交易占比 | 盈利交易数/总交易数 |
| 盈亏比 | 平均盈利/平均亏损 | - |
| 最大连续亏损 | 最长连续亏损次数 | - |

#### 回测流程

```mermaid
sequenceDiagram
participant Client as 客户端
participant API as API网关
participant Adapter as 回测适配器
participant Framework as 外部框架
participant Data as 市场数据
Client->>API : POST /api/v1/backtest/run
API->>Adapter : 创建适配器实例
Adapter->>Framework : 初始化回测框架
Framework->>Data : 加载历史数据
Data-->>Framework : 返回数据
Framework->>Framework : 执行回测
Framework-->>Adapter : 返回交易记录
Adapter->>Adapter : 计算回测指标
Adapter-->>API : 返回回测结果
API-->>Client : 返回JSON响应
```

**图表来源**
- [app/services/backtest.py:161-260](file://app/services/backtest.py#L161-L260)

### 回测接口规范

#### 运行回测 (POST /api/v1/backtest/run)

##### 请求规范

| 参数名 | 描述 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|------|--------|------|
| framework | 回测框架 | string | 是 | - | qstrader/pyalgotrade/custom |
| initial_capital | 初始资金 | number | 是 | > 0 | - |
| commission_rate | 佣金费率 | number | 否 | 0.001 | 0.1% |
| slippage_model | 滑点模型 | string | 否 | "fixed" | fixed/percentage/volatility |
| data | 市场数据 | object | 是 | - | {ticker: DataFrame} |

##### 响应结构

**响应示例**
```json
{
  "success": true,
  "framework": "qstrader",
  "initial_capital": 100000,
  "final_capital": 125000,
  "metrics": {
    "total_return": 25.0,
    "sharpe_ratio": 1.2,
    "max_drawdown": 15.5,
    "win_rate": 60.0,
    "profit_factor": 1.8,
    "total_trades": 45
  },
  "trade_count": 45,
  "equity_curve": [100000, 102000, 105000, ...]
}
```

#### 获取可用框架 (GET /api/v1/backtest/frameworks)

##### 响应结构

**响应示例**
```json
{
  "available_frameworks": ["qstrader", "pyalgotrade"],
  "installed_packages": ["qstrader", "pyalgotrade"],
  "missing_packages": []
}
```

**章节来源**
- [app/services/backtest.py:33-487](file://app/services/backtest.py#L33-L487)

## 测试API端点

### 开发测试工具

系统提供专门的测试API端点，便于开发和调试：

#### 快速测试脚本

系统包含多个测试脚本，用于验证核心功能：

- **quick_test.py**: 快速策略引擎测试
- **test_analyze.py**: 完整分析流程测试
- **test_api.py**: API端点自动化测试

#### 测试脚本功能

##### quick_test.py
- 生成60天测试数据
- 执行完整策略分析
- 验证头寸计算逻辑
- 输出详细测试结果

##### test_analyze.py
- 生成100天测试数据
- 执行完整分析流程
- 验证所有返回指标
- 生成详细分析报告

##### test_api.py
- 自动化API端点测试
- 覆盖健康检查、分析、历史、持仓等端点
- 验证错误处理机制
- 支持pytest框架运行

**章节来源**
- [scripts/quick_test.py:1-50](file://scripts/quick_test.py#L1-L50)
- [scripts/test_analyze.py:1-62](file://scripts/test_analyze.py#L1-L62)
- [tests/test_api.py:1-269](file://tests/test_api.py#L1-L269)

## 数据模型规范

### 请求模型

#### AnalyzeRequest (分析请求)

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| ticker | string | 是 | - | 资产代码，自动转为大写 |
| account_equity | float | 是 | - | 账户净资产，必须>0 |
| period | string | 否 | "1y" | 数据周期 |
| dollar_per_point | float | 否 | 1.0 | 每点美元价值 |

#### PositionAddRequest (添加持仓请求)

| 字段 | 类型 | 必要 | 默认值 | 说明 |
|------|------|------|--------|------|
| ticker | string | 是 | - | 资产代码 |
| position_type | enum | 是 | - | "LONG" 或 "SHORT" |
| shares | float | 是 | - | 持仓股数，必须>0 |
| entry_price | float | 是 | - | 入场价格，必须>0 |
| n_value | float | 是 | - | 入场时N值，必须>0 |

### 响应模型

#### AnalyzeResponse (分析响应)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 分析是否成功 |
| ticker | string | 是 | 资产代码 |
| analysis_time | datetime | 是 | 分析时间 |
| current_price | float | 是 | 当前收盘价 |
| previous_close | float | 否 | 前一日收盘价 |
| price_change | float | 否 | 价格变动 |
| price_change_pct | float | 否 | 价格变动百分比 |
| signal | enum | 是 | 交易信号 |
| signal_detail | object | 是 | 信号详情对象 |
| channel_levels | object | 是 | 通道水平对象 |
| volatility | object | 是 | 波动率数据对象 |
| recommendation | object | 是 | 持仓建议对象 |
| risk_metrics | object | 是 | 风险指标对象 |
| price_history | array | 是 | 历史价格数据数组 |
| error | string | 否 | 错误信息 |

#### 历史记录模型

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 记录ID |
| ticker | string | 是 | 资产代码 |
| analysis_time | datetime | 是 | 分析时间 |
| current_price | float | 是 | 当前价格 |
| signal | enum | 是 | 交易信号 |
| signal_reason | string | 否 | 信号原因 |
| high_20_day | float | 否 | 20日最高价 |
| low_10_day | float | 否 | 10日最低价 |
| n_value | float | 否 | N值 |
| recommended_units | float | 否 | 建议单位数 |
| position_size | float | 否 | 建议持仓大小 |
| account_equity | float | 是 | 账户净资产 |
| is_active | boolean | 是 | 是否活跃信号 |

#### 回测结果模型

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| total_return | float | 是 | 总收益率(%) |
| sharpe_ratio | float | 是 | 夏普比率 |
| max_drawdown | float | 是 | 最大回撤(%) |
| win_rate | float | 是 | 胜率(%) |
| profit_factor | float | 是 | 盈亏比 |
| total_trades | integer | 是 | 总交易数 |
| avg_trade_return | float | 是 | 平均交易收益(%) |
| max_consecutive_losses | integer | 是 | 最大连续亏损 |
| annual_return | float | 是 | 年化收益率(%) |
| volatility | float | 是 | 波动率(%) |

**章节来源**
- [app/schemas/trading.py:30-262](file://app/schemas/trading.py#L30-L262)

## 错误处理与状态码

### HTTP状态码规范

| 状态码 | 描述 | 使用场景 |
|--------|------|----------|
| 200 | OK | 请求成功，返回正常响应 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误或验证失败 |
| 401 | Unauthorized | 未认证或认证失败 |
| 403 | Forbidden | 权限不足 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务不可用 |

### 错误响应格式

```json
{
  "success": false,
  "error": "错误描述信息",
  "error_code": "错误代码",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 全局异常处理

系统提供全局异常处理器，统一处理未捕获的异常：

```mermaid
flowchart TD
Exception[异常发生] --> GlobalHandler[全局异常处理器]
GlobalHandler --> Log[记录日志]
GlobalHandler --> ErrorResponse[返回标准错误响应]
ErrorResponse --> Client[客户端]
```

**图表来源**
- [app/main.py:71-82](file://app/main.py#L71-L82)

**章节来源**
- [app/main.py:71-82](file://app/main.py#L71-L82)

## 性能优化建议

### 缓存策略

系统采用多层次缓存机制：

1. **数据库查询缓存**: 使用SQLAlchemy的查询缓存功能
2. **API响应缓存**: 对历史查询结果进行短期缓存
3. **计算结果缓存**: 对重复的策略计算结果进行缓存
4. **回测结果缓存**: 对历史回测结果进行缓存

### 数据库优化

```mermaid
graph TD
subgraph "数据库优化"
Indexing[索引优化] --> QueryPlan[查询计划]
QueryPlan --> ConnectionPool[连接池管理]
ConnectionPool --> AsyncOps[异步操作]
AsyncOps --> Performance[性能提升]
end
```

**图表来源**
- [app/database/models.py:61-65](file://app/database/models.py#L61-L65)

### 并发处理

- **异步处理**: 所有API端点支持异步处理
- **连接池管理**: 数据库连接池自动管理
- **限流机制**: 防止API滥用和资源耗尽
- **速率限制**: 基于IP的请求频率控制

**章节来源**
- [app/database/models.py:61-65](file://app/database/models.py#L61-L65)

## OpenAPI规范

### API文档生成

系统自动生成OpenAPI规范和交互式文档：

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

### API版本管理

系统使用版本化的API前缀：
- **当前版本**: `/api/v1`

### 数据验证

所有API请求都经过严格的Pydantic验证：

```mermaid
flowchart LR
Request[HTTP请求] --> Pydantic[Pydantic验证]
Pydantic --> Schema[数据模式验证]
Schema --> Valid[验证通过]
Schema --> Invalid[验证失败]
Valid --> Handler[业务处理]
Invalid --> Error[返回错误]
```

**图表来源**
- [app/schemas/trading.py:30-72](file://app/schemas/trading.py#L30-L72)

**章节来源**
- [app/main.py:33-59](file://app/main.py#L33-L59)

## 客户端实现指南

### 基础HTTP客户端

```javascript
// JavaScript示例
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 策略分析
async function analyzeAsset(ticker, accountEquity) {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + localStorage.getItem('access_token')
    },
    body: JSON.stringify({
      ticker,
      account_equity: accountEquity,
      period: '1y'
    })
  });
  
  return response.json();
}

// 获取历史记录
async function getHistory(params) {
  const queryString = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/history?${queryString}`, {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('access_token')
    }
  });
  return response.json();
}

// 用户登录
async function login(username, password) {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username,
      password
    })
  });
  
  const data = await response.json();
  if (data.access_token) {
    localStorage.setItem('access_token', data.access_token);
  }
  
  return data;
}
```

### 错误处理最佳实践

```javascript
// 错误处理示例
async function robustApiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error || 'API returned error');
    }
    
    return data;
  } catch (error) {
    console.error('API调用失败:', error);
    throw error;
  }
}
```

### 重试机制

```javascript
// 重试机制示例
async function retryApiCall(fn, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      // 指数退避
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
    }
  }
}
```

### 认证处理

```javascript
// 认证处理示例
class APIClient {
  constructor() {
    this.baseURL = 'http://localhost:8000';
    this.token = localStorage.getItem('access_token');
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    if (response.status === 401) {
      // Token过期，刷新Token
      await this.refreshToken();
      return this.request(endpoint, options);
    }
    
    return response.json();
  }
  
  async refreshToken() {
    const response = await fetch('/auth/test-token?user_id=1');
    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('access_token', data.access_token);
  }
}
```

## 部署与监控

### 系统健康检查

```mermaid
graph TD
HealthCheck[健康检查] --> Database[数据库连接]
HealthCheck --> DataSources[数据源可用性]
HealthCheck --> APIEndpoints[API端点可用性]
HealthCheck --> Security[安全组件]
Database --> StatusOK[状态正常]
Database --> StatusError[状态异常]
DataSources --> StatusOK
DataSources --> StatusError
APIEndpoints --> StatusOK
APIEndpoints --> StatusError
Security --> StatusOK
Security --> StatusError
```

**图表来源**
- [app/main.py:91-99](file://app/main.py#L91-L99)

### 监控指标

系统提供以下监控指标：

- **API响应延迟**: 分布式统计
- **吞吐量**: 每秒请求数
- **错误率**: HTTP 5xx错误比例
- **数据库连接**: 连接池使用情况
- **缓存命中率**: 查询缓存效率
- **安全事件**: 认证失败和权限拒绝次数

### 部署建议

1. **生产环境配置**: 设置适当的CORS策略和安全配置
2. **数据库优化**: 配置合适的连接池大小和超时设置
3. **监控告警**: 设置关键指标的告警阈值
4. **日志管理**: 配置结构化日志输出和轮转
5. **安全加固**: 配置HTTPS和安全头
6. **回测环境**: 为回测框架安装必要的依赖包

**章节来源**
- [app/main.py:91-99](file://app/main.py#L91-L99)
- [app/core/config.py:11-99](file://app/core/config.py#L11-L99)