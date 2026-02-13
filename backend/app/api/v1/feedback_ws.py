"""
反馈WebSocket路由
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.feedback_ws import feedback_ws_manager

router = APIRouter()

@router.websocket("/ws/feedback")
async def feedback_websocket(websocket: WebSocket, client_type: str = "agent"):
    """
    反馈WebSocket连接端点
    
    客户端连接示例:
    ws://localhost:8000/api/v1/ws/feedback?client_type=agent
    
    消息格式:
    - 客户端发送: {"type": "pong"} - 响应心跳
    - 客户端发送: {"type": "subscribe", "channel": "feedback"} - 订阅频道
    - 客户端发送: {"type": "mark_read", "feedback_id": 123} - 标记已读
    
    - 服务端发送: {"type": "ping", "timestamp": "..."} - 心跳包
    - 服务端发送: {"type": "new_feedback", "data": {...}, "timestamp": "..."} - 新反馈通知
    - 服务端发送: {"type": "feedback_read", "feedback_id": 123, "timestamp": "..."} - 已读通知
    """
    await feedback_ws_manager.connect(websocket, client_type)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            await feedback_ws_manager.handle_message(websocket, data)
            
    except WebSocketDisconnect:
        feedback_ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"[WebSocket] 连接异常: {e}")
        feedback_ws_manager.disconnect(websocket)
