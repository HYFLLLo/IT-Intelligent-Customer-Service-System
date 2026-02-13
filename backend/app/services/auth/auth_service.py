from datetime import datetime, timedelta
import jwt
import bcrypt
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.config.settings import settings
from typing import Optional, Dict, Any

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        Args:
            plain_password: 原始密码
            hashed_password: 哈希后的密码
            
        Returns:
            密码是否正确
        """
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间
            
        Returns:
            JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌
        
        Args:
            token: JWT token
            
        Returns:
            解码后的数据，如果验证失败则返回None
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def register_user(db: Session, username: str, email: str, password: str, role: UserRole = UserRole.EMPLOYEE, department: Optional[str] = None) -> User:
        """注册用户
        
        Args:
            db: 数据库会话
            username: 用户名
            email: 邮箱
            password: 密码
            role: 用户角色
            department: 部门
            
        Returns:
            创建的用户对象
        """
        # 检查用户名是否已存在
        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            raise ValueError("用户名或邮箱已存在")
        
        # 哈希密码
        hashed_password = AuthService.hash_password(password)
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role,
            department=department,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """认证用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            认证成功的用户对象，如果失败则返回None
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户对象，如果不存在则返回None
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象，如果不存在则返回None
        """
        return db.query(User).filter(User.username == username).first()