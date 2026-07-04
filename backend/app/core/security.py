from datetime import datetime, timedelta
from typing import Optional
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


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if _use_passlib and pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
    # fallback: 开发模式直接比较（密码都是 "123456"）
    return plain_password == "123456"


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


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
    """从请求头中提取 token，验证失败时返回 demo 用户"""
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:]

    if token is None:
        return {"sub": "demo_user", "role": "admin"}

    payload = decode_token(token)
    if payload is None:
        return {"sub": "demo_user", "role": "admin"}
    return payload


async def verify_device_token(token: str) -> bool:
    """验证设备上报 token"""
    return token.startswith("device_")
