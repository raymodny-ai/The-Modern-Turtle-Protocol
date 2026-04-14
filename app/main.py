"""
现代海龟协议量化交易系统
FastAPI主应用入口
"""

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.security import (
    get_current_user,
    RBACChecker,
    audit_logger,
    create_test_token,
    User
)
from app.database.session import init_db
from app.api import analyze, history, positions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    print("📊 正在初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时执行
    print("👋 关闭应用...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## 现代海龟协议量化交易系统 API

基于经典海龟交易法则的自动化量化交易系统后端服务。

### 核心功能

- 📈 **策略分析**: 基于波动率的趋势跟踪信号生成
- 💰 **头寸计算**: 动态风险管理的头寸规模计算
- 📊 **历史追踪**: 完整的交易决策历史记录
- 🔔 **信号通知**: BUY/SELL信号实时推送

### 海龟协议核心参数

- **入场周期**: 20日最高价突破
- **出场周期**: 10日最低价跌破
- **风险控制**: 每笔交易1%账户风险
- **N值**: 20日ATR真实波幅
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "path": str(request.url)
        }
    )


# 注册路由
app.include_router(analyze.router, prefix=settings.API_V1_PREFIX)
app.include_router(history.router, prefix=settings.API_V1_PREFIX)
app.include_router(positions.router, prefix=settings.API_V1_PREFIX)


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """API根路径"""
    return {
        "message": "欢迎使用现代海龟协议量化交易系统",
        "docs": "/docs",
        "version": settings.APP_VERSION
    }


# ============================================
# 认证相关端点 (PRD第5.3章AuthTuna安全网关)
# ============================================

@app.post("/auth/login", tags=["认证"])
async def login(username: str, password: str):
    """
    用户登录
    
    返回JWT访问令牌
    """
    # 简化验证（实际应查数据库）
    user_db = get_user_db()
    
    for user_id, user in user_db.users.items():
        if user.username == username:
            if user_db.verify_password(user_id, password):
                token = user_db.create_access_token(user_id, settings.SECRET_KEY)
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "role": user.role.value
                }
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误"
    )


@app.get("/auth/me", tags=["认证"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "permissions": RBACChecker.get_role_permissions(current_user.role)
    }


@app.get("/auth/test-token", tags=["认证"])
async def get_test_token(user_id: int = 1):
    """
    获取测试Token（仅开发环境使用）
    
    符合PRD第5.3章AuthTuna安全框架集成
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅在开发环境下可用"
        )
    
    token = create_test_token(user_id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "note": "仅用于开发测试"
    }


@app.get("/audit/logs", tags=["审计"])
async def get_audit_logs(
    limit: int = 100,
    current_user: User = Depends(RBACChecker.require_permissions(["users:read"]))
):
    """
    获取安全审计日志
    
    仅管理员可访问
    """
    return {
        "logs": audit_logger.get_recent_logs(limit)
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
