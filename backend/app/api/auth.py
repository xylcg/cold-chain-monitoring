"""
认证 API
"""
from fastapi import APIRouter, HTTPException, Depends
from ..schemas import LoginRequest, TokenResponse
from ..core.security import verify_password, create_access_token, get_current_user
from datetime import timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# 模拟用户数据库 - 4 种角色
MOCK_USERS = {
    "admin": {
        "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O",
        "role": "admin",
        "username": "admin",
    },
    "driver01": {
        "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O",
        "role": "driver",
        "username": "driver01",
    },
    "warehouse01": {
        "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O",
        "role": "warehouse",
        "username": "warehouse01",
    },
    "customer01": {
        "password_hash": "$2b$12$LJ3m4ys3Lk0TSwHCpNqrFOsD5qhQZ0YHJzC6uPqjE0dSx4Oq5mP3O",
        "role": "customer",
        "username": "customer01",
    },
}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    user = MOCK_USERS.get(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 开发模式：接受密码 "123456"
    if request.password != "123456" and not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(
        data={"sub": request.username, "role": user["role"]},
        expires_delta=timedelta(hours=8),
    )

    return TokenResponse(
        access_token=access_token,
        user_role=user["role"],
        username=request.username,
    )


@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "username": user.get("sub"),
        "role": user.get("role"),
        "exp": user.get("exp"),
    }
