"""
用户反馈API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

from app.database import get_db
from app.models.feedback import UserFeedback, FeedbackSession
from app.models.user import User
from app.websocket.feedback_ws import feedback_ws_manager

router = APIRouter(tags=["feedback"])


# ============ 数据模型 ============

class FeedbackCreate(BaseModel):
    """创建反馈请求模型"""
    session_id: str
    feedback_type: str  # satisfied, dissatisfied
    question_text: str
    answer_text: str
    issue_options: Optional[List[str]] = None
    detailed_description: Optional[str] = None
    device_info: Optional[str] = None
    browser_info: Optional[str] = None
    answer_generated_at: Optional[str] = None
    submit_duration_ms: Optional[int] = None


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    id: int
    user_id: int
    session_id: str
    feedback_type: str
    question_text: str
    answer_text: str
    issue_options: Optional[List[str]]
    detailed_description: Optional[str]
    device_info: Optional[str]
    browser_info: Optional[str]
    feedback_submitted_at: str
    is_read: bool
    is_processed: bool
    
    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """反馈列表响应"""
    total: int
    items: List[FeedbackResponse]


class FeedbackSessionCheck(BaseModel):
    """检查会话反馈状态响应"""
    session_id: str
    feedback_shown: bool
    feedback_submitted: bool


class FeedbackStats(BaseModel):
    """反馈统计"""
    total_count: int
    satisfied_count: int
    dissatisfied_count: int
    satisfaction_rate: float
    unread_count: int


# ============ 员工侧API ============

@router.post("/submit", response_model=dict)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """提交用户反馈"""
    # 验证 feedback_type 不为空
    if not feedback.feedback_type:
        raise HTTPException(status_code=400, detail="反馈类型不能为空")
    
    # 验证 feedback_type 必须是有效的值
    if feedback.feedback_type not in ["satisfied", "dissatisfied"]:
        raise HTTPException(status_code=400, detail=f"无效的反馈类型: {feedback.feedback_type}")
    
    try:
        # 创建反馈记录
        db_feedback = UserFeedback(
            user_id=1,  # 暂时使用固定用户ID，后续从认证中获取
            session_id=feedback.session_id,
            feedback_type=feedback.feedback_type,
            question_text=feedback.question_text,
            answer_text=feedback.answer_text,
            issue_options=feedback.issue_options,
            detailed_description=feedback.detailed_description,
            device_info=feedback.device_info,
            browser_info=feedback.browser_info,
            answer_generated_at=datetime.fromisoformat(feedback.answer_generated_at) if feedback.answer_generated_at else None,
            submit_duration_ms=feedback.submit_duration_ms
        )

        db.add(db_feedback)
        db.flush()  # 获取ID但不提交

        # 更新会话记录
        session_record = db.query(FeedbackSession).filter(
            FeedbackSession.session_id == feedback.session_id
        ).first()

        if session_record:
            session_record.feedback_submitted = True
            session_record.submitted_at = datetime.now()
        else:
            # 创建新的会话记录
            session_record = FeedbackSession(
                session_id=feedback.session_id,
                user_id=1,
                feedback_shown=True,
                shown_at=datetime.now(),
                feedback_submitted=True,
                submitted_at=datetime.now()
            )
            db.add(session_record)

        db.commit()

        # 通过WebSocket通知坐席端有新反馈
        feedback_data = {
            "id": db_feedback.id,
            "feedback_type": db_feedback.feedback_type,
            "question_text": db_feedback.question_text[:50] + "..." if len(db_feedback.question_text) > 50 else db_feedback.question_text,
            "feedback_submitted_at": db_feedback.feedback_submitted_at.isoformat() if db_feedback.feedback_submitted_at else None
        }
        await feedback_ws_manager.notify_new_feedback(feedback_data)

        return {
            "success": True,
            "message": "反馈提交成功",
            "feedback_id": db_feedback.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/session/{session_id}/check", response_model=FeedbackSessionCheck)
def check_session_feedback(session_id: str, db: Session = Depends(get_db)):
    """检查会话是否已显示或提交反馈"""
    session_record = db.query(FeedbackSession).filter(
        FeedbackSession.session_id == session_id
    ).first()
    
    if session_record:
        return FeedbackSessionCheck(
            session_id=session_id,
            feedback_shown=session_record.feedback_shown,
            feedback_submitted=session_record.feedback_submitted
        )
    
    return FeedbackSessionCheck(
        session_id=session_id,
        feedback_shown=False,
        feedback_submitted=False
    )


@router.post("/session/{session_id}/mark-shown")
def mark_session_shown(session_id: str, db: Session = Depends(get_db)):
    """标记会话反馈窗口已显示"""
    try:
        session_record = db.query(FeedbackSession).filter(
            FeedbackSession.session_id == session_id
        ).first()
        
        if session_record:
            session_record.feedback_shown = True
            session_record.shown_at = datetime.now()
        else:
            session_record = FeedbackSession(
                session_id=session_id,
                user_id=1,
                feedback_shown=True,
                shown_at=datetime.now()
            )
            db.add(session_record)
        
        db.commit()
        return {"success": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"标记失败: {str(e)}")


# ============ 坐席侧API ============

@router.get("/list", response_model=FeedbackListResponse)
def get_feedback_list(
    feedback_type: Optional[str] = Query(None, description="反馈类型: satisfied/dissatisfied"),
    time_range: Optional[str] = Query("all", description="时间范围: today/yesterday/week/month/all"),
    is_read: Optional[bool] = Query(None),
    is_processed: Optional[bool] = Query(None, description="是否已处理"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取反馈列表（坐席侧）"""
    query = db.query(UserFeedback)

    # 筛选条件
    if feedback_type:
        query = query.filter(UserFeedback.feedback_type == feedback_type)

    if time_range:
        now = datetime.now()
        if time_range == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(UserFeedback.created_at >= start_time)
        elif time_range == "yesterday":
            start_time = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(UserFeedback.created_at >= start_time, UserFeedback.created_at < end_time)
        elif time_range == "week":
            start_time = now - timedelta(days=7)
            query = query.filter(UserFeedback.created_at >= start_time)
        elif time_range == "month":
            start_time = now - timedelta(days=30)
            query = query.filter(UserFeedback.created_at >= start_time)

    if is_read is not None:
        query = query.filter(UserFeedback.is_read == is_read)

    if is_processed is not None:
        query = query.filter(UserFeedback.is_processed == is_processed)
    
    if search:
        query = query.filter(
            UserFeedback.question_text.contains(search) |
            UserFeedback.answer_text.contains(search) |
            UserFeedback.detailed_description.contains(search)
        )
    
    # 排序和分页
    total = query.count()
    items = query.order_by(desc(UserFeedback.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return FeedbackListResponse(
        total=total,
        items=[FeedbackResponse(
            id=item.id,
            user_id=item.user_id,
            session_id=item.session_id,
            feedback_type=item.feedback_type,
            question_text=item.question_text,
            answer_text=item.answer_text,
            issue_options=item.issue_options,
            detailed_description=item.detailed_description,
            device_info=item.device_info,
            browser_info=item.browser_info,
            feedback_submitted_at=item.feedback_submitted_at.isoformat() if item.feedback_submitted_at else "",
            is_read=item.is_read,
            is_processed=item.is_processed
        ) for item in items]
    )


@router.get("/stats", response_model=FeedbackStats)
def get_feedback_stats(db: Session = Depends(get_db)):
    """获取反馈统计"""
    total = db.query(UserFeedback).count()
    satisfied = db.query(UserFeedback).filter(UserFeedback.feedback_type == "satisfied").count()
    dissatisfied = db.query(UserFeedback).filter(UserFeedback.feedback_type == "dissatisfied").count()
    unread = db.query(UserFeedback).filter(UserFeedback.is_read == False).count()
    
    satisfaction_rate = (satisfied / total * 100) if total > 0 else 0
    
    return FeedbackStats(
        total_count=total,
        satisfied_count=satisfied,
        dissatisfied_count=dissatisfied,
        satisfaction_rate=round(satisfaction_rate, 2),
        unread_count=unread
    )


@router.post("/{feedback_id}/mark-read")
def mark_feedback_read(feedback_id: int, db: Session = Depends(get_db)):
    """标记反馈为已读"""
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    feedback.is_read = True
    db.commit()
    
    return {"success": True}


@router.post("/{feedback_id}/mark-processed")
def mark_feedback_processed(
    feedback_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """标记反馈为已处理"""
    feedback = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    feedback.is_processed = True
    feedback.processed_at = datetime.now()
    feedback.processed_by = 1  # 暂时使用固定用户ID
    feedback.process_notes = notes
    db.commit()
    
    return {"success": True}


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """获取未读反馈数量"""
    count = db.query(UserFeedback).filter(UserFeedback.is_read == False).count()
    return {"unread_count": count}
