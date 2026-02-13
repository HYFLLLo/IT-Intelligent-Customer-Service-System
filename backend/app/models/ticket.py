from sqlalchemy import Column, Integer, String, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from ..database import Base

class TicketStatus(PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

class TicketPriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketSource(PyEnum):
    EMPLOYEE_CREATED = "employee_created"  # 员工主动创建
    TRANSFERRED = "transferred"  # 转人工创建

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.PENDING)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    source = Column(Enum(TicketSource), nullable=False, default=TicketSource.TRANSFERRED)  # 工单来源
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)
    resolved_at = Column(String(20), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tickets", foreign_keys=[user_id])
    assigned_agent = relationship("User", back_populates="assigned_tickets", foreign_keys=[assigned_agent_id])
    responses = relationship("TicketResponse", back_populates="ticket", cascade="all, delete-orphan")
    quality_checks = relationship("QualityCheck", back_populates="ticket", cascade="all, delete-orphan")

class TicketResponse(Base):
    __tablename__ = "ticket_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(String(20), nullable=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="responses")
    agent = relationship("User")