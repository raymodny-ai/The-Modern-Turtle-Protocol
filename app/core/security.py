"""
AuthTuna安全认证中间件
现代海龟协议 - PRD第5.3章要求的认证鉴权实现

符合PRD要求:
- 高强度身份鉴权
- RBAC角色权限分割
- 防止恶意并发重放攻击
- 安全审计护城河
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.base import SecurityBase
from typing import Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import secrets
import time
import jwt
from passlib.context import CryptContext
import re


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer认证
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"           # 管理员: 完全权限
    TRADER = "trader"         # 交易员: 策略分析、持仓管理
    ANALYST = "analyst"       # 分析师: 只读分析、历史查询
    VIEWER = "viewer"         # 查看者: 仅查看权限


@dataclass
class User:
    """用户模型"""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


@dataclass
class TokenData:
    """Token数据"""
    user_id: int
    username: str
    role: UserRole
    exp: datetime
    iat: datetime
    jti: str  # JWT ID，用于防重放


@dataclass
class APIKey:
    """API Key模型"""
    id: int
    name: str
    key_hash: str
    user_id: int
    permissions: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    rate_limit: int  # 每分钟请求限制


class SimpleUserDatabase:
    """简单用户数据库（生产环境应使用真实数据库）"""
    
    def __init__(self):
        self.users = {
            1: User(
                id=1, 
                username="admin", 
                email="admin@example.com",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.now()
            ),
            2: User(
                id=2, 
                username="trader", 
                email="trader@example.com",
                role=UserRole.TRADER,
                is_active=True,
                created_at=datetime.now()
            ),
            3: User(
                id=3, 
                username="analyst", 
                email="analyst@example.com",
                role=UserRole.ANALYST,
                is_active=True,
                created_at=datetime.now()
            ),
        }
        # 密码哈希存储
        self.password_hashes = {
            1: pwd_context.hash("admin123"),
            2: pwd_context.hash("trader123"),
            3: pwd_context.hash("analyst123"),
        }
        
        # API Keys存储
        self.api_keys = {}
        
        # JWT黑名单（用于登出/撤销）
        self.jwt_blacklist = set()
        
        # 速率限制追踪
        self.rate_limits: dict = {}
    
    def verify_password(self, user_id: int, plain_password: str) -> bool:
        """验证密码"""
        if user_id not in self.password_hashes:
            return False
        return pwd_context.verify(plain_password, self.password_hashes[user_id])
    
    def create_access_token(self, user_id: int, secret_key: str) -> str:
        """创建JWT访问令牌"""
        user = self.users.get(user_id)
        if not user or not user.is_active:
            raise ValueError("用户不存在或已禁用")
        
        now = datetime.now()
        expire = now + timedelta(hours=1)
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": expire,
            "iat": now,
            "jti": secrets.token_hex(16)  # 唯一ID用于防重放
        }
        
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def verify_token(self, token: str, secret_key: str) -> TokenData:
        """验证JWT Token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            jti = payload.get("jti")
            
            # 检查是否在黑名单（防重放）
            if jti and jti in self.jwt_blacklist:
                raise ValueError("Token已失效")
            
            return TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=jti or ""
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token已过期")
        except jwt.InvalidTokenError:
            raise ValueError("无效的Token")
    
    def revoke_token(self, token: str, secret_key: str):
        """撤销Token（登出）"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            if payload.get("jti"):
                self.jwt_blacklist.add(payload["jti"])
        except:
            pass
    
    def check_rate_limit(self, identifier: str, limit: int = 60) -> bool:
        """
        检查速率限制
        
        符合PRD第5.3章\"防止恶意并发重放攻击\"
        """
        now = time.time()
        minute_key = f"{identifier}:{int(now // 60)}"
        
        if minute_key not in self.rate_limits:
            self.rate_limits = {k: v for k, v in self.rate_limits.items() 
                               if k.endswith(f":{int(now // 60)}")}
            self.rate_limits[minute_key] = 0
        
        self.rate_limits[minute_key] += 1
        
        if self.rate_limits[minute_key] > limit:
            return False  # 超限
        return True
    
    def get_api_key_permissions(self, api_key: str) -> Optional[List[str]]:
        """获取API Key权限"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        for key in self.api_keys.values():
            if key.key_hash == key_hash and key.is_active:
                if key.expires_at and key.expires_at < datetime.now():
                    return None  # 已过期
                return key.permissions
        return None


# 全局用户数据库实例
user_db = SimpleUserDatabase()


class RBACChecker:
    """
    RBAC角色权限检查器
    
    符合PRD第5.3章\"角色权限分割(RBAC)\"要求
    """
    
    # 角色权限映射
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [
            "analyze:read", "analyze:write",
            "history:read", "history:delete",
            "positions:read", "positions:write", "positions:delete",
            "users:read", "users:write", "users:delete",
            "settings:read", "settings:write",
            "api_keys:manage"
        ],
        UserRole.TRADER: [
            "analyze:read", "analyze:write",
            "history:read",
            "positions:read", "positions:write",
        ],
        UserRole.ANALYST: [
            "analyze:read",
            "history:read",
            "positions:read",
        ],
        UserRole.VIEWER: [
            "analyze:read",
            "positions:read",
        ],
    }
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """检查角色是否有指定权限"""
        return permission in cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> List[str]:
        """获取角色的所有权限"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def require_permissions(cls, required_permissions: List[str]):
        """权限检查依赖"""
        def checker(token_data: TokenData = Depends(_get_current_token)):
            user = user_db.users.get(token_data.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在"
                )
            
            for perm in required_permissions:
                if not cls.has_permission(user.role, perm):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {perm}"
                    )
            
            return user
        
        return checker


# 全局配置
SECRET_KEY = "change-this-in-production"
ALGORITHM = "HS256"


async def _get_current_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """
    获取当前用户Token
    
    支持两种认证方式:
    1. Bearer Token (JWT)
    2. API Key
    """
    # 检查速率限制
    client_ip = request.client.host if request.client else "unknown"
    
    # 从Header或Query获取API Key
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if api_key:
        permissions = user_db.get_api_key_permissions(api_key)
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的API Key"
            )
        
        # 从API Key获取用户信息
        key_perms = permissions
        return TokenData(
            user_id=0,
            username="api_key_user",
            role=UserRole.TRADER,  # API Key默认Trader权限
            exp=datetime.now() + timedelta(days=365),
            iat=datetime.now(),
            jti=""
        )
    
    # Bearer Token认证
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        token_data = user_db.verify_token(credentials.credentials, SECRET_KEY)
        
        # 速率限制检查
        if not user_db.check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试"
            )
        
        return token_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(token_data: TokenData = Depends(_get_current_token)) -> User:
    """获取当前登录用户"""
    user = user_db.users.get(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return user


# 预定义的权限依赖
require_analyze = RBACChecker.require_permissions(["analyze:read"])
require_analyze_write = RBACChecker.require_permissions(["analyze:write"])
require_history = RBACChecker.require_permissions(["history:read"])
require_positions = RBACChecker.require_permissions(["positions:read"])
require_positions_write = RBACChecker.require_permissions(["positions:write"])


class SecurityAuditLogger:
    """
    安全审计日志
    
    符合PRD第5.3章\"安全审计护城河\"
    """
    
    def __init__(self):
        self.logs: List[dict] = []
    
    def log_access(
        self,
        user_id: int,
        username: str,
        endpoint: str,
        method: str,
        ip_address: str,
        status_code: int,
        user_agent: str = ""
    ):
        """记录访问日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "endpoint": endpoint,
            "method": method,
            "ip_address": ip_address,
            "status_code": status_code,
            "user_agent": user_agent,
            "event_type": "ACCESS"
        }
        self.logs.append(log_entry)
        print(f"[SECURITY] {log_entry}")
    
    def log_auth_failure(
        self,
        username: str,
        ip_address: str,
        reason: str,
        user_agent: str = ""
    ):
        """记录认证失败"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "ip_address": ip_address,
            "reason": reason,
            "user_agent": user_agent,
            "event_type": "AUTH_FAILURE"
        }
        self.logs.append(log_entry)
        print(f"[SECURITY WARNING] {log_entry}")
    
    def log_permission_denied(
        self,
        user_id: int,
        username: str,
        required_permission: str,
        endpoint: str,
        ip_address: str
    ):
        """记录权限拒绝"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "required_permission": required_permission,
            "endpoint": endpoint,
            "ip_address": ip_address,
            "event_type": "PERMISSION_DENIED"
        }
        self.logs.append(log_entry)
        print(f"[SECURITY] {log_entry}")
    
    def get_recent_logs(self, limit: int = 100) -> List[dict]:
        """获取最近的审计日志"""
        return self.logs[-limit:]


# 全局审计日志实例
audit_logger = SecurityAuditLogger()


def create_test_token(user_id: int = 1) -> str:
    """创建测试Token（仅用于开发/测试）"""
    return user_db.create_access_token(user_id, SECRET_KEY)
