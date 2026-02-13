from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth.auth_service import AuthService
from app.models.user import User

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前用户
    
    Args:
        token: JWT token
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 如果认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = AuthService.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前活跃用户对象
    """
    # 这里可以添加额外的检查，比如用户是否被禁用
    return current_user


async def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前管理员用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前管理员用户对象
        
    Raises:
        HTTPException: 如果用户不是管理员
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    return current_user


async def get_current_agent(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前客服用户
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前客服用户对象
        
    Raises:
        HTTPException: 如果用户不是客服
    """
    if current_user.role.value != "agent" and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要客服权限"
        )
    return current_user