from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from .config import get_settings

settings = get_settings()

# bcrypt/passlib 兼容性问题，使用简单的 hash 比较作为 fallback
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _use_passlib = True
except Exception:
    pwd_context = None
    _use_passlib = False

# 模拟用户数据库（开发环境）
_MOCK_USERS = {
    "admin": {"password_hash": "", "role": "admin", "name": "管理员"},
    "boss": {"password_hash": "", "role": "admin", "name": "老板"},
    "warehouse01": {"password_hash": "", "role": "warehouse", "name": "仓管员01"},
    "warehouse02": {"password_hash": "", "role": "warehouse", "name": "仓管员02"},
    "driver01": {"password_hash": "", "role": "driver", "name": "司机张三"},
    "driver02": {"password_hash": "", "role": "driver", "name": "司机李四"},
    "customer01": {"password_hash": "", "role": "customer", "name": "客户01"},
    "customer02": {"password_hash": "", "role": "customer", "name": "客户02"},
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 优先使用 bcrypt，开发环境兼容明文"""
    if _use_passlib and pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    # 开发模式：如果哈希为空（未初始化）或明文比较
    if not hashed_password:
        return plain_password == "123456"
    return plain_password == hashed_password


def get_password_hash(password: str) -> str:
    if _use_passlib and pwd_context:
        return pwd_context.hash(password)
    return password  # 开发环境回退


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(request: Request) -> dict:
    """
    从请求头中提取 JWT token 并验证。
    **安全修复**: 不再在无 token 时返回 admin 角色，必须提供有效 token。
    """
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否存在于模拟数据库
    username = payload.get("sub", "")
    if username and username not in _MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户 '{username}' 不存在",
        )

    return payload


def require_role(*allowed_roles: str):
    """
    角色权限检查依赖注入工厂。
    用法: Depends(require_role("admin", "warehouse"))
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: 需要 {', '.join(allowed_roles)} 角色，当前角色为 {user_role}",
            )
        return user
    return role_checker


async def verify_device_token(token: str) -> bool:
    """验证设备上报 token"""
    return token.startswith("device_")


def get_mock_users() -> dict:
    """获取模拟用户列表"""
    return _MOCK_USERS
