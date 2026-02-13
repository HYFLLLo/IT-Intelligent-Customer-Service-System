"""
反馈WebSocket管理器
用于实时推送新反馈通知
"""
from typing import List, Dict
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

class FeedbackWebSocketManager:
    """反馈WebSocket连接管理器"""
    
    def __init__(self):
        # 存储所有活跃的WebSocket连接
        self.active_connections: List[WebSocket] = []
        # 存储每个连接的订阅信息
        self.connection_metadata: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, client_type: str = "agent"):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = {
            "client_type": client_type,
            "connected_at": datetime.now().isoformat(),
            "client_id": id(websocket)
        }
        print(f"[WebSocket] 新连接已建立 - 类型: {client_type}, 总连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            print(f"[WebSocket] 连接已断开 - 剩余连接数: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """向特定连接发送消息"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            print(f"[WebSocket] 发送消息失败: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, client_type: str = None):
        """广播消息给所有或特定类型的客户端"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                # 如果指定了client_type，只发送给该类型的客户端
                if client_type:
                    conn_meta = self.connection_metadata.get(connection, {})
                    if conn_meta.get("client_type") != client_type:
                        continue
                
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print(f"[WebSocket] 广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def notify_new_feedback(self, feedback_data: dict):
        """通知所有坐席端有新反馈"""
        message = {
            "type": "new_feedback",
            "data": feedback_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message, client_type="agent")
        print(f"[WebSocket] 已广播新反馈通知 - 反馈ID: {feedback_data.get('id')}")
    
    async def notify_feedback_read(self, feedback_id: int):
        """通知反馈已读状态更新"""
        message = {
            "type": "feedback_read",
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message, client_type="agent")
    
    async def send_ping(self, websocket: WebSocket):
        """发送心跳包"""
        try:
            await websocket.send_text(json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()}))
        except Exception as e:
            print(f"[WebSocket] 发送心跳失败: {e}")
            self.disconnect(websocket)
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "pong":
                # 客户端响应心跳
                pass
            elif msg_type == "subscribe":
                # 更新订阅信息
                channel = data.get("channel")
                if websocket in self.connection_metadata:
                    self.connection_metadata[websocket]["channel"] = channel
                    print(f"[WebSocket] 客户端订阅频道: {channel}")
            elif msg_type == "mark_read":
                # 客户端标记反馈已读
                feedback_id = data.get("feedback_id")
                if feedback_id:
                    await self.notify_feedback_read(feedback_id)
            else:
                print(f"[WebSocket] 未知消息类型: {msg_type}")
                
        except json.JSONDecodeError:
            print(f"[WebSocket] 收到无效的JSON消息: {message}")
        except Exception as e:
            print(f"[WebSocket] 处理消息时出错: {e}")
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        stats = {
            "total_connections": len(self.active_connections),
            "agent_connections": 0,
            "employee_connections": 0,
            "other_connections": 0
        }
        
        for conn_meta in self.connection_metadata.values():
            client_type = conn_meta.get("client_type", "unknown")
            if client_type == "agent":
                stats["agent_connections"] += 1
            elif client_type == "employee":
                stats["employee_connections"] += 1
            else:
                stats["other_connections"] += 1
        
        return stats

# 创建全局WebSocket管理器实例
feedback_ws_manager = FeedbackWebSocketManager()
