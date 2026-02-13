"""
埋点数据模型
IT Intelligent Customer Service System - Analytics Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, JSON
from sqlalchemy.sql import func
from app.database import Base
import json


class AnalyticsEvent(Base):
    """埋点事件数据表"""
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(50), unique=True, index=True, nullable=False, comment="事件唯一ID")
    event_type = Column(String(50), nullable=False, index=True, comment="事件类型")
    event_name = Column(String(200), nullable=False, index=True, comment="事件名称")
    timestamp = Column(Integer, nullable=False, index=True, comment="事件时间戳(毫秒)")
    session_id = Column(String(100), nullable=False, index=True, comment="会话ID")

    # 用户信息
    user_id = Column(String(100), nullable=True, index=True, comment="用户ID")
    user_role = Column(String(50), nullable=True, index=True, comment="用户角色")
    user_department = Column(String(100), nullable=True, comment="用户部门")

    # 页面信息
    page_url = Column(String(500), nullable=True, comment="页面URL")
    page_title = Column(String(200), nullable=True, comment="页面标题")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    ip_address = Column(String(50), nullable=True, comment="IP地址")

    # 事件数据（JSON格式）
    event_data = Column(Text, nullable=True, comment="事件详细数据(JSON)")

    # 数据库记录时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录创建时间")

    # 索引优化
    __table_args__ = (
        Index('idx_analytics_time_type', 'timestamp', 'event_type'),
        Index('idx_analytics_user_time', 'user_id', 'timestamp'),
        Index('idx_analytics_session', 'session_id', 'timestamp'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.event_id,
            "eventType": self.event_type,
            "eventName": self.event_name,
            "timestamp": self.timestamp,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "userDepartment": self.user_department,
            "pageUrl": self.page_url,
            "pageTitle": self.page_title,
            "userAgent": self.user_agent,
            "ipAddress": self.ip_address,
            "data": json.loads(self.event_data) if self.event_data else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.event_id}, type={self.event_type}, name={self.event_name})>"


class AnalyticsDailyStats(Base):
    """埋点数据统计表（按天聚合）"""
    __tablename__ = "analytics_daily_stats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stat_date = Column(String(10), nullable=False, index=True, unique=True, comment="统计日期(YYYY-MM-DD)")

    # 总体统计
    total_events = Column(Integer, default=0, comment="总事件数")
    unique_users = Column(Integer, default=0, comment="独立用户数")
    unique_sessions = Column(Integer, default=0, comment="独立会话数")

    # 事件类型分布
    page_view_count = Column(Integer, default=0, comment="页面浏览数")
    click_count = Column(Integer, default=0, comment="点击事件数")
    api_count = Column(Integer, default=0, comment="API调用数")
    error_count = Column(Integer, default=0, comment="错误数")
    business_count = Column(Integer, default=0, comment="业务事件数")

    # 业务事件统计
    submit_question_count = Column(Integer, default=0, comment="提交问题数")
    create_ticket_count = Column(Integer, default=0, comment="创建工单数")
    rate_response_count = Column(Integer, default=0, comment="评价回复数")

    # 性能统计
    avg_page_load_time = Column(Float, default=0, comment="平均页面加载时间(ms)")
    avg_api_response_time = Column(Float, default=0, comment="平均API响应时间(ms)")

    # 用户角色分布
    employee_events = Column(Integer, default=0, comment="员工端事件数")
    agent_events = Column(Integer, default=0, comment="坐席端事件数")
    admin_events = Column(Integer, default=0, comment="管理端事件数")

    # 详细数据（JSON格式）
    details = Column(Text, nullable=True, comment="详细统计数据(JSON)")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """转换为字典"""
        return {
            "statDate": self.stat_date,
            "totalEvents": self.total_events,
            "uniqueUsers": self.unique_users,
            "uniqueSessions": self.unique_sessions,
            "eventTypeDistribution": {
                "pageView": self.page_view_count,
                "click": self.click_count,
                "api": self.api_count,
                "error": self.error_count,
                "business": self.business_count
            },
            "businessEvents": {
                "submitQuestion": self.submit_question_count,
                "createTicket": self.create_ticket_count,
                "rateResponse": self.rate_response_count
            },
            "userRoleDistribution": {
                "employee": self.employee_events,
                "agent": self.agent_events,
                "admin": self.admin_events
            },
            "performance": {
                "avgPageLoadTime": self.avg_page_load_time,
                "avgApiResponseTime": self.avg_api_response_time
            },
            "details": json.loads(self.details) if self.details else None
        }


class AnalyticsEventType:
    """事件类型常量"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    API = "api"
    ERROR = "error"
    PERFORMANCE = "performance"
    BUSINESS = "business"


class BusinessEventType:
    """业务事件类型常量"""
    SUBMIT_QUESTION = "submit_question"
    CREATE_TICKET = "create_ticket"
    RATE_RESPONSE = "rate_response"


class UserRole:
    """用户角色常量"""
    EMPLOYEE = "employee"
    AGENT = "agent"
    ADMIN = "admin"
