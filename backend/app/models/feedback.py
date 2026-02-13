"""
用户反馈模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database import Base


class UserFeedback(Base):
    """用户反馈表"""
    __tablename__ = "user_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), nullable=False, index=True)
    
    # 反馈类型: satisfied(满意), dissatisfied(不满意)
    feedback_type = Column(String(20), nullable=False)
    
    # 关联的问题和回答
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    
    # 不满意反馈的详细信息
    issue_options = Column(JSON, nullable=True)  # ["inaccurate", "misunderstood", "slow"]
    detailed_description = Column(Text, nullable=True)
    
    # 设备信息
    device_info = Column(String(200), nullable=True)
    browser_info = Column(String(200), nullable=True)
    
    # 时间戳
    answer_generated_at = Column(DateTime, nullable=True)
    feedback_submitted_at = Column(DateTime, server_default=func.now())
    submit_duration_ms = Column(Integer, nullable=True)  # 从回答生成到反馈提交的时长(毫秒)
    
    # 处理状态
    is_read = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    process_notes = Column(Text, nullable=True)
    
    # 创建时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FeedbackSession(Base):
    """反馈会话记录表 - 用于防止重复弹出"""
    __tablename__ = "feedback_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 是否已经显示过反馈窗口
    feedback_shown = Column(Boolean, default=False)
    shown_at = Column(DateTime, nullable=True)
    
    # 是否已经提交反馈
    feedback_submitted = Column(Boolean, default=False)
    submitted_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
