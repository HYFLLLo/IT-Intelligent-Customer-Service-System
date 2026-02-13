from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class KnowledgeCategory(Base):
    __tablename__ = "knowledge_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)
    
    # Relationships
    documents = relationship("KnowledgeDocument", back_populates="category", cascade="all, delete-orphan", primaryjoin="KnowledgeCategory.id == KnowledgeDocument.category_id")

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("knowledge_categories.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(200), nullable=True)
    created_at = Column(String(20), nullable=True)
    updated_at = Column(String(20), nullable=True)
    
    # Relationships
    category = relationship("KnowledgeCategory", back_populates="documents")