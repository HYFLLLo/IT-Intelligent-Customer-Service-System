from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class QuestionHistory(Base):
    __tablename__ = "question_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    confidence = Column(String(10), nullable=True)
    created_at = Column(String(20), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="questions")