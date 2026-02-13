from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.services.auth.auth_service import AuthService
from app.services.auth.auth_dependency import get_current_active_user
from app.models.user import User, UserRole
from app.config.settings import settings

router = APIRouter()


class UserCreate(BaseModel):
    """用户创建模型"""
    username: str
    email: str
    password: str
    role: Optional[str] = "employee"
    department: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    role: str
    department: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册接口
    
    Args:
        user: 用户注册信息
        db: 数据库会话
        
    Returns:
        创建的用户信息
    """
    try:
        # 验证角色
        role_map = {
            "employee": UserRole.EMPLOYEE,
            "agent": UserRole.AGENT,
            "admin": UserRole.ADMIN
        }
        
        role = role_map.get(user.role, UserRole.EMPLOYEE)
        
        # 注册用户
        created_user = AuthService.register_user(
            db=db,
            username=user.username,
            email=user.email,
            password=user.password,
            role=role,
            department=user.department
        )
        
        return UserResponse(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            role=created_user.role.value,
            department=created_user.department,
            created_at=created_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册用户时发生错误: {str(e)}"
        )


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录接口
    
    Args:
        form_data: OAuth2密码表单数据
        db: 数据库会话
        
    Returns:
        访问令牌和用户信息
    """
    # 认证用户
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            department=user.department,
            created_at=user.created_at
        )
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前用户信息
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        department=current_user.department,
        created_at=current_user.created_at
    )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_active_user)):
    """用户登出接口
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        登出结果
    """
    # 在实际应用中，这里可以添加令牌黑名单等逻辑
    return {"message": "登出成功"}