from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class QualityCheck(Base):
    __tablename__ = "quality_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    check_time = Column(String(20), nullable=True)
    score = Column(String(10), nullable=True)
    comments = Column(Text, nullable=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="quality_checks")

class QualityRule(Base):
    __tablename__ = "quality_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(String(10), nullable=True)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)