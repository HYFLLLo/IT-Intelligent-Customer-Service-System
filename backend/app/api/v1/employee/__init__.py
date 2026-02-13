from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.rag import RAGService
from app.services.ticket.workflow import TicketWorkflow
from app.services.auth.auth_dependency import get_current_active_user
from app.models.user import User
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter()


class QuestionRequest(BaseModel):
    """问题请求模型"""
    question: str
    category: Optional[str] = None


class QuestionResponse(BaseModel):
    """问题响应模型"""
    answer: str
    confidence: float
    suggestion: Optional[str] = None


class TicketRequest(BaseModel):
    """工单请求模型"""
    title: str
    description: str
    priority: Optional[str] = "medium"
    category: Optional[str] = None
    device_info: Optional[str] = None
    system_info: Optional[str] = None
    user: Optional[str] = None
    department: Optional[str] = None
    source: Optional[str] = "employee_created"  # 工单来源: employee_created(员工主动创建), transferred(转人工)


class TicketResponse(BaseModel):
    """工单响应模型"""
    id: int
    title: str
    content: str
    status: str
    priority: str
    user_id: int
    assigned_agent_id: Optional[int] = None
    category: Optional[str] = None
    created_at: str
    updated_at: str


class TicketStatusUpdate(BaseModel):
    """工单状态更新模型"""
    ticket_id: int
    status: str


class NotificationResponse(BaseModel):
    """通知响应模型"""
    id: int
    type: str
    title: str
    content: str
    response: Optional[str] = None
    is_read: bool
    created_at: str
    report_id: Optional[int] = None
    ticket_id: Optional[int] = None
    score: Optional[int] = None
    report_data: Optional[dict] = None  # 完整的质检报告数据


from fastapi.responses import StreamingResponse
import asyncio

@router.post("/question", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    """智能问答接口
    
    Args:
        request: 问题请求参数
        
    Returns:
        问题回答和置信度
    """
    try:
        rag_service = RAGService()
        # 员工端使用简洁版回答
        result = rag_service.ask_question(
            query=request.question,
            category=request.category,
            concise=True
        )
        response = QuestionResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            suggestion=result.get("suggestion")
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理问题时发生错误: {str(e)}")


@router.post("/question/stream")
async def ask_question_stream(request: QuestionRequest):
    """智能问答流式接口
    
    Args:
        request: 问题请求参数
        
    Returns:
        流式回答
    """
    async def generate():
        try:
            # 获取完整回答（员工端使用简洁版）
            rag_service = RAGService()
            result = rag_service.ask_question(
                query=request.question,
                category=request.category,
                concise=True
            )
            answer = result["answer"]
            confidence = result["confidence"]
            suggestion = result.get("suggestion")
            
            # 检查是否是错误消息
            if "抱歉，AI服务暂时不可用" in answer:
                # 直接返回错误信息
                yield f"data: {json.dumps({'error': 'AI服务暂时不可用，请稍后再试或提交工单获取帮助。'})}\n\n"
                return
            
            # 流式发送回答 - 按字符流式输出，模拟打字效果
            chunk_size = 10  # 每10个字符发送一次
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                # 使用JSON格式发送，避免格式问题
                yield f"data: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0.03)  # 模拟流式输出
            
            # 发送结束标记和置信度
            yield f"data: {json.dumps({'end': True, 'confidence': confidence, 'suggestion': suggestion})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/ticket", response_model=TicketResponse)
def create_ticket(request: TicketRequest, db: Session = Depends(get_db)):
    """创建工单接口
    
    Args:
        request: 工单请求参数
        db: 数据库会话
        
    Returns:
        创建的工单信息
    """
    try:
        workflow = TicketWorkflow(db)
        content = request.description
        if request.device_info:
            content += f"\n设备信息: {request.device_info}"
        if request.system_info:
            content += f"\n系统信息: {request.system_info}"
        if request.user:
            content += f"\n用户: {request.user}"
        if request.department:
            content += f"\n部门: {request.department}"
        # 使用默认用户ID 1（临时解决方案）
        # 根据请求中的 source 字段标记工单来源
        ticket = workflow.create_ticket(
            title=request.title,
            content=content,
            user_id=1,
            priority=request.priority,
            category=request.category,
            source=request.source
        )
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            content=ticket.content,
            status=ticket.status.value,
            priority=ticket.priority.value,
            user_id=ticket.user_id,
            assigned_agent_id=ticket.assigned_agent_id,
            category=ticket.category,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工单时发生错误: {str(e)}")


@router.get("/tickets", response_model=List[TicketResponse])
def get_user_tickets(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """获取用户工单列表
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        用户的工单列表
    """
    try:
        from app.services.ticket.status_manager import StatusManager
        status_manager = StatusManager(db)
        tickets = status_manager.get_tickets_by_user(user_id=current_user.id)
        return [
            TicketResponse(
                id=ticket.id,
                title=ticket.title,
                content=ticket.content,
                status=ticket.status.value,
                priority=ticket.priority.value,
                user_id=ticket.user_id,
                assigned_agent_id=ticket.assigned_agent_id,
                category=ticket.category,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at
            )
            for ticket in tickets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工单列表时发生错误: {str(e)}")


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_detail(ticket_id: int, db: Session = Depends(get_db)):
    """获取工单详情
    
    Args:
        ticket_id: 工单ID
        db: 数据库会话
        
    Returns:
        工单详细信息
    """
    try:
        from app.services.ticket.workflow import TicketWorkflow
        workflow = TicketWorkflow(db)
        ticket = workflow.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在")
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            content=ticket.content,
            status=ticket.status.value,
            priority=ticket.priority.value,
            user_id=ticket.user_id,
            assigned_agent_id=ticket.assigned_agent_id,
            category=ticket.category,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工单详情时发生错误: {str(e)}")


@router.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """重新打开工单
    
    Args:
        ticket_id: 工单ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        workflow = TicketWorkflow(db)
        ticket = workflow.reopen_ticket(ticket_id, user_id=current_user.id)
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在或无法重新打开")
        return {"message": "工单已重新打开", "ticket_id": ticket.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新打开工单时发生错误: {str(e)}")


@router.get("/notifications", response_model=List[NotificationResponse])
def get_user_notifications(db: Session = Depends(get_db)):
    """获取用户通知列表
    
    Args:
        db: 数据库会话
        
    Returns:
        用户的通知列表
    """
    try:
        from app.models.user import Notification
        import json
        
        # 暂时使用用户ID 1，后续可以从身份验证中获取
        notifications = db.query(Notification).filter(Notification.user_id == 1).order_by(Notification.created_at.desc()).all()
        
        # 检查Notification模型是否有response字段和report_data字段
        has_response_field = hasattr(Notification, 'response')
        has_report_data_field = hasattr(Notification, 'report_data')
        
        result = []
        for notification in notifications:
            # 解析report_data JSON
            report_data = None
            if has_report_data_field and notification.report_data:
                try:
                    report_data = json.loads(notification.report_data)
                except json.JSONDecodeError:
                    report_data = None
            
            result.append(NotificationResponse(
                id=notification.id,
                type=notification.type,
                title=notification.title,
                content=notification.content,
                response=notification.response if has_response_field else None,
                is_read=notification.is_read,
                created_at=notification.created_at,
                report_id=notification.report_id,
                ticket_id=notification.ticket_id,
                score=notification.score,
                report_data=report_data  # 包含完整的质检报告数据
            ))
        
        return result
    except Exception as e:
        # 如果发生错误，返回空列表
        print(f"获取通知列表失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return []


@router.post("/notifications/{notification_id}/read")
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    """标记通知为已读
    
    Args:
        notification_id: 通知ID
        db: 数据库会话
        
    Returns:
        操作结果
    """
    try:
        from app.models.user import Notification
        # 暂时使用用户ID 1，后续可以从身份验证中获取
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == 1
        ).first()
        
        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")
        
        notification.is_read = True
        db.commit()
        
        return {"message": "通知已标记为已读", "notification_id": notification.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记通知为已读时发生错误: {str(e)}")


@router.get("/notifications/unread-count")
def get_unread_notification_count(db: Session = Depends(get_db)):
    """获取未读通知数量
    
    Args:
        db: 数据库会话
        
    Returns:
        未读通知数量
    """
    try:
        from app.models.user import Notification
        # 暂时使用用户ID 1，后续可以从身份验证中获取
        count = db.query(Notification).filter(
            Notification.user_id == 1,
            Notification.is_read == False
        ).count()
        
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未读通知数量时发生错误: {str(e)}")
