from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from ..database import Base

class UserRole(PyEnum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    AGENT = "agent"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    department = Column(String(50), nullable=True)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)
    
    # Relationships
    notifications = relationship("Notification", back_populates="user")
    tickets = relationship("Ticket", back_populates="user", foreign_keys="Ticket.user_id")
    assigned_tickets = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")
    questions = relationship("QuestionHistory", back_populates="user")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # quality_report, ticket_update, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(String(20), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    # 额外字段，用于存储质检报告详情
    report_id = Column(Integer, nullable=True)
    ticket_id = Column(Integer, nullable=True)
    score = Column(Integer, nullable=True)
    
    # 新增字段：存储完整质检报告数据（JSON格式）
    report_data = Column(Text, nullable=True)  # 存储完整的质检报告JSON数据