"""数据库初始化脚本"""
import sys
from app.database import engine, Base, SessionLocal

# 先导入所有模型，避免循环引用
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus, TicketPriority, TicketResponse
from app.models.quality import QualityCheck, QualityRule
from app.models.knowledge import KnowledgeCategory, KnowledgeDocument

from app.services.auth.auth_service import AuthService

# 创建所有表
Base.metadata.create_all(bind=engine)

# 创建数据库会话
db = SessionLocal()

try:
    # 检查是否已存在用户
    existing_user = db.query(User).first()
    if not existing_user:
        # 创建默认员工用户
        employee_user = AuthService.register_user(
            db=db,
            username="employee",
            email="employee@example.com",
            password="password123",
            role=UserRole.EMPLOYEE,
            department="IT"
        )
        print(f"创建默认员工用户: {employee_user.username}")
        
        # 创建默认客服用户
        agent_user = AuthService.register_user(
            db=db,
            username="agent",
            email="agent@example.com",
            password="password123",
            role=UserRole.AGENT,
            department="客服"
        )
        print(f"创建默认客服用户: {agent_user.username}")
        
        # 创建默认管理员用户
        admin_user = AuthService.register_user(
            db=db,
            username="admin",
            email="admin@example.com",
            password="password123",
            role=UserRole.ADMIN,
            department="管理"
        )
        print(f"创建默认管理员用户: {admin_user.username}")
    else:
        print("数据库中已存在用户，跳过初始化")
finally:
    db.close()

print("数据库初始化完成!")
