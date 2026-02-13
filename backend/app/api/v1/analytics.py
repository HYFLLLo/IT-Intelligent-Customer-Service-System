"""
埋点数据接收API
IT Intelligent Customer Service System - Analytics API
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import json
import time

from app.database import get_db, SessionLocal
from app.models.analytics import AnalyticsEvent as AnalyticsEventModel, AnalyticsDailyStats
from app.models.analytics import AnalyticsEventType, UserRole

router = APIRouter()


# ========== 请求模型 ==========

class TrackEvent(BaseModel):
    """单个埋点事件"""
    id: Optional[str] = None
    eventType: str = Field(..., description="事件类型")
    eventName: str = Field(..., description="事件名称")
    timestamp: int = Field(..., description="事件时间戳(毫秒)")
    sessionId: str = Field(..., description="会话ID")
    userId: Optional[str] = Field(None, description="用户ID")
    userRole: Optional[str] = Field(None, description="用户角色")
    userDepartment: Optional[str] = Field(None, description="用户部门")
    pageUrl: str = Field(..., description="页面URL")
    pageTitle: Optional[str] = Field(None, description="页面标题")
    userAgent: Optional[str] = Field(None, description="用户代理")
    data: Optional[Dict[str, Any]] = Field(None, description="事件数据")


class BatchTrackRequest(BaseModel):
    """批量埋点请求"""
    events: List[TrackEvent]


class AnalyticsQueryParams(BaseModel):
    """埋点数据查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=1000, description="每页数量")
    event_type: Optional[str] = Field(None, description="事件类型筛选")
    event_name: Optional[str] = Field(None, description="事件名称筛选")
    user_id: Optional[str] = Field(None, description="用户ID筛选")
    user_role: Optional[str] = Field(None, description="用户角色筛选")
    user_department: Optional[str] = Field(None, description="部门筛选")
    start_time: Optional[int] = Field(None, description="开始时间戳(毫秒)")
    end_time: Optional[int] = Field(None, description="结束时间戳(毫秒)")
    keyword: Optional[str] = Field(None, description="关键词搜索")


# ========== 响应模型 ==========

class AnalyticsEventResponse(BaseModel):
    """埋点事件响应"""
    id: str
    eventType: str
    eventName: str
    timestamp: int
    sessionId: str
    userId: Optional[str]
    userRole: Optional[str]
    userDepartment: Optional[str]
    pageUrl: str
    pageTitle: Optional[str]
    data: Optional[Dict[str, Any]]
    createdAt: Optional[str]


class AnalyticsListResponse(BaseModel):
    """埋点列表响应"""
    total: int
    page: int
    page_size: int
    data: List[AnalyticsEventResponse]


class AnalyticsOverview(BaseModel):
    """埋点概览统计"""
    total_events: int
    today_events: int
    unique_users: int
    event_type_distribution: Dict[str, int]
    top_events: List[Dict[str, Any]]
    recent_events: List[AnalyticsEventResponse]


class BusinessEventStats(BaseModel):
    """业务事件统计"""
    submit_question_count: int
    create_ticket_count: int
    rate_response_count: int
    avg_question_duration: float
    avg_ticket_duration: float


# ========== API端点 ==========

@router.post("/analytics")
async def collect_analytics(
    request: BatchTrackRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    接收前端埋点数据（批量）
    """
    # 获取客户端IP
    client_ip = http_request.headers.get("X-Forwarded-For", http_request.client.host)

    # 后台异步保存数据
    background_tasks.add_task(save_events_batch, request.events, client_ip)

    return {"status": "ok", "received": len(request.events)}


@router.get("/analytics", response_model=AnalyticsListResponse)
async def query_analytics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None),
    user_department: Optional[str] = Query(None),
    start_time: Optional[int] = Query(None),
    end_time: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    查询埋点数据（支持多维度筛选）
    仅返回员工端业务事件：提交问题、创建工单、评价回复
    """
    query = db.query(AnalyticsEventModel)

    # 只查询业务事件类型
    query = query.filter(AnalyticsEventModel.event_type == "business")

    # 应用筛选条件
    if event_type:
        query = query.filter(AnalyticsEventModel.event_type == event_type)

    if event_name:
        query = query.filter(AnalyticsEventModel.event_name.contains(event_name))

    if user_id:
        query = query.filter(AnalyticsEventModel.user_id == user_id)

    if user_role:
        query = query.filter(AnalyticsEventModel.user_role == user_role)

    if user_department:
        query = query.filter(AnalyticsEventModel.user_department == user_department)

    if start_time:
        query = query.filter(AnalyticsEventModel.timestamp >= start_time)

    if end_time:
        query = query.filter(AnalyticsEventModel.timestamp <= end_time)

    if keyword:
        query = query.filter(
            or_(
                AnalyticsEventModel.event_name.contains(keyword),
                AnalyticsEventModel.user_id.contains(keyword),
                AnalyticsEventModel.page_url.contains(keyword)
            )
        )

    # 计算总数
    total = query.count()

    # 分页查询
    events = query.order_by(desc(AnalyticsEventModel.timestamp)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [event.to_dict() for event in events]
    }


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    获取埋点数据概览统计
    """
    # 计算时间范围
    end_time = int(time.time() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)

    today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

    # 总体统计
    total_events = db.query(AnalyticsEventModel).filter(
        AnalyticsEventModel.timestamp >= start_time
    ).count()

    today_events = db.query(AnalyticsEventModel).filter(
        AnalyticsEventModel.timestamp >= today_start
    ).count()

    # 独立用户数
    unique_users = db.query(AnalyticsEventModel.user_id).filter(
        AnalyticsEventModel.timestamp >= start_time
    ).distinct().count()

    # 事件类型分布
    type_distribution = db.query(
        AnalyticsEventModel.event_type,
        func.count(AnalyticsEventModel.id).label("count")
    ).filter(
        AnalyticsEventModel.timestamp >= start_time
    ).group_by(AnalyticsEventModel.event_type).all()

    # Top 10 事件
    top_events = db.query(
        AnalyticsEventModel.event_name,
        func.count(AnalyticsEventModel.id).label("count")
    ).filter(
        AnalyticsEventModel.timestamp >= start_time
    ).group_by(AnalyticsEventModel.event_name).order_by(
        desc("count")
    ).limit(10).all()

    # 最近事件
    recent_events = db.query(AnalyticsEventModel).order_by(
        desc(AnalyticsEventModel.timestamp)
    ).limit(5).all()

    return {
        "total_events": total_events,
        "today_events": today_events,
        "unique_users": unique_users,
        "event_type_distribution": {item[0]: item[1] for item in type_distribution},
        "top_events": [{"eventName": item[0], "count": item[1]} for item in top_events],
        "recent_events": [event.to_dict() for event in recent_events]
    }


@router.get("/analytics/business-stats", response_model=BusinessEventStats)
async def get_business_event_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    获取业务事件统计（员工侧）
    """
    end_time = int(time.time() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)

    # 提交问题统计
    submit_question_events = db.query(AnalyticsEventModel).filter(
        and_(
            AnalyticsEventModel.event_name == "submit_question",
            AnalyticsEventModel.timestamp >= start_time
        )
    ).all()

    # 创建工单统计
    create_ticket_events = db.query(AnalyticsEventModel).filter(
        and_(
            AnalyticsEventModel.event_name == "create_ticket",
            AnalyticsEventModel.timestamp >= start_time
        )
    ).all()

    # 评价回复统计
    rate_response_events = db.query(AnalyticsEventModel).filter(
        and_(
            AnalyticsEventModel.event_name == "rate_response",
            AnalyticsEventModel.timestamp >= start_time
        )
    ).all()

    # 计算平均耗时
    question_durations = []
    for event in submit_question_events:
        if event.event_data:
            data = json.loads(event.event_data)
            if data and "submitDuration" in data:
                question_durations.append(data["submitDuration"])

    ticket_durations = []
    for event in create_ticket_events:
        if event.event_data:
            data = json.loads(event.event_data)
            if data and "duration" in data:
                ticket_durations.append(data["duration"])

    return {
        "submit_question_count": len(submit_question_events),
        "create_ticket_count": len(create_ticket_events),
        "rate_response_count": len(rate_response_events),
        "avg_question_duration": sum(question_durations) / len(question_durations) if question_durations else 0,
        "avg_ticket_duration": sum(ticket_durations) / len(ticket_durations) if ticket_durations else 0
    }


@router.get("/analytics/export")
async def export_analytics(
    start_time: int = Query(..., description="开始时间戳(毫秒)"),
    end_time: int = Query(..., description="结束时间戳(毫秒)"),
    event_type: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    导出埋点数据（Excel格式）
    返回数据供前端生成Excel
    """
    query = db.query(AnalyticsEventModel).filter(
        and_(
            AnalyticsEventModel.timestamp >= start_time,
            AnalyticsEventModel.timestamp <= end_time
        )
    )

    if event_type:
        query = query.filter(AnalyticsEventModel.event_type == event_type)

    if user_role:
        query = query.filter(AnalyticsEventModel.user_role == user_role)

    # 限制导出数量
    events = query.order_by(desc(AnalyticsEventModel.timestamp)).limit(100000).all()

    # 转换为导出格式
    export_data = []
    for event in events:
        event_dict = event.to_dict()
        export_data.append({
            "事件ID": event_dict["id"],
            "事件类型": event_dict["eventType"],
            "事件名称": event_dict["eventName"],
            "发生时间": datetime.fromtimestamp(event_dict["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            "会话ID": event_dict["sessionId"],
            "用户ID": event_dict["userId"] or "",
            "用户角色": event_dict["userRole"] or "",
            "部门": event_dict["userDepartment"] or "",
            "页面URL": event_dict["pageUrl"],
            "页面标题": event_dict["pageTitle"] or "",
            "详细数据": json.dumps(event_dict["data"], ensure_ascii=False) if event_dict["data"] else ""
        })

    return {
        "total": len(export_data),
        "data": export_data
    }


@router.post("/analytics/clear")
async def clear_all_analytics(
    db: Session = Depends(get_db)
):
    """
    清除所有埋点记录
    """
    try:
        # 获取删除前的记录数
        count = db.query(AnalyticsEventModel).count()

        # 删除所有记录
        db.query(AnalyticsEventModel).delete()
        db.commit()

        return {
            "status": "ok",
            "message": f"已清除 {count} 条埋点记录",
            "deleted_count": count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清除失败: {str(e)}")


# ========== 后台任务 ==========

def save_events_batch(events: List[TrackEvent], client_ip: str):
    """
    批量保存埋点事件到数据库
    """
    db = SessionLocal()
    try:
        for event in events:
            db_event = AnalyticsEventModel(
                event_id=event.id or f"evt_{int(time.time() * 1000)}",
                event_type=event.eventType,
                event_name=event.eventName,
                timestamp=event.timestamp,
                session_id=event.sessionId,
                user_id=event.userId,
                user_role=event.userRole,
                user_department=event.userDepartment,
                page_url=event.pageUrl,
                page_title=event.pageTitle,
                user_agent=event.userAgent,
                ip_address=client_ip,
                event_data=json.dumps(event.data, ensure_ascii=False) if event.data else None
            )
            db.add(db_event)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Analytics] Failed to save events: {e}")
    finally:
        db.close()
