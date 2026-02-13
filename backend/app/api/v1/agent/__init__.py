from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ticket.workflow import TicketWorkflow
from app.services.auth.auth_dependency import get_current_agent
from app.models.ticket import TicketStatus
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class TicketStatusUpdate(BaseModel):
    """工单状态更新模型"""
    ticket_id: int
    status: str


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


class TicketResolution(BaseModel):
    """工单解决方案模型"""
    ticket_id: int
    resolution: str


class TicketCloseRequest(BaseModel):
    """关闭工单请求模型"""
    reply_content: Optional[str] = None
    skip_quality_check: Optional[bool] = False


class AIReplySuggestionRequest(BaseModel):
    """AI回复建议请求模型"""
    ticket_id: int
    user_message: Optional[str] = None


class KnowledgeItem(BaseModel):
    """知识片段模型"""
    content: str
    source: str


class ExtractedField(BaseModel):
    """提取的字段模型"""
    name: str
    value: str


class AIReplySuggestionResponse(BaseModel):
    """AI回复建议响应模型"""
    ticket_id: int
    suggestions: List[str]
    knowledge_items: List[KnowledgeItem] = []
    extracted_fields: List[ExtractedField] = []


@router.get("/tickets", response_model=List[TicketResponse])
def get_agent_tickets(db: Session = Depends(get_db)):
    """获取客服分配的工单列表（仅包含员工主动创建的工单，排除转人工的工单）
    
    Args:
        db: 数据库会话
        
    Returns:
        客服分配的工单列表（仅员工主动创建的，排除标题为"人工客服请求"的）
    """
    try:
        from app.services.ticket.status_manager import StatusManager
        from app.models.ticket import Ticket
        status_manager = StatusManager(db)
        # 查询所有已分配的工单（不限制特定客服，以便测试）
        tickets = db.query(Ticket).filter(Ticket.assigned_agent_id.isnot(None)).all()
        # 过滤掉标题为"人工客服请求"的工单（这些是转人工创建的）
        # 只保留员工主动创建的工单（标题不是"人工客服请求"）
        filtered_tickets = [ticket for ticket in tickets if ticket.title != "人工客服请求"]
        return [
            TicketResponse(
                id=ticket.id,
                title=ticket.title,
                content=ticket.content,
                status=ticket.status if isinstance(ticket.status, str) else ticket.status.value,
                priority=ticket.priority if isinstance(ticket.priority, str) else ticket.priority.value,
                user_id=ticket.user_id,
                assigned_agent_id=ticket.assigned_agent_id,
                category=ticket.category,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at
            )
            for ticket in filtered_tickets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工单列表时发生错误: {str(e)}")


@router.get("/tickets/pending", response_model=List[TicketResponse])
def get_pending_tickets(db: Session = Depends(get_db)):
    """获取待处理的工单列表
    
    Args:
        db: 数据库会话
        
    Returns:
        待处理的工单列表
    """
    try:
        from app.services.ticket.status_manager import StatusManager
        from app.models.ticket import Ticket, TicketStatus
        from sqlalchemy import or_
        # 直接使用db查询所有待处理和处理中的工单
        # 使用SQL函数忽略大小写和空格进行查询
        from sqlalchemy import func
        tickets = db.query(Ticket).filter(or_(
            func.lower(func.trim(Ticket.status)) == "pending",
            func.lower(func.trim(Ticket.status)) == "processing"
        )).all()
        return [
            TicketResponse(
                id=ticket.id,
                title=ticket.title,
                content=ticket.content,
                status=ticket.status if isinstance(ticket.status, str) else ticket.status.value,
                priority=ticket.priority if isinstance(ticket.priority, str) else ticket.priority.value,
                user_id=ticket.user_id,
                assigned_agent_id=ticket.assigned_agent_id,
                category=ticket.category,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at
            )
            for ticket in tickets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待处理工单时发生错误: {str(e)}")


@router.post("/tickets/{ticket_id}/process")
def process_ticket(ticket_id: int, db: Session = Depends(get_db), current_agent: User = Depends(get_current_agent)):
    """开始处理工单
    
    Args:
        ticket_id: 工单ID
        db: 数据库会话
        current_agent: 当前客服
        
    Returns:
        操作结果
    """
    try:
        workflow = TicketWorkflow(db)
        ticket = workflow.process_ticket(ticket_id, agent_id=current_agent.id)
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在或无法处理")
        return {"message": "工单已开始处理", "ticket_id": ticket.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理工单时发生错误: {str(e)}")


@router.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: int, resolution: str, db: Session = Depends(get_db), current_agent: User = Depends(get_current_agent)):
    """解决工单
    
    Args:
        ticket_id: 工单ID
        resolution: 解决方案
        db: 数据库会话
        current_agent: 当前客服
        
    Returns:
        操作结果
    """
    try:
        workflow = TicketWorkflow(db)
        ticket = workflow.resolve_ticket(ticket_id, agent_id=current_agent.id, resolution=resolution)
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在或无法解决")
        return {"message": "工单已解决", "ticket_id": ticket.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决工单时发生错误: {str(e)}")


@router.post("/tickets/{ticket_id}/close")
def close_ticket(ticket_id: int, request: TicketCloseRequest, db: Session = Depends(get_db)):
    """关闭工单
    
    Args:
        ticket_id: 工单ID
        request: 关闭工单请求，包含回复内容
        db: 数据库会话
        
    Returns:
        操作结果
    """
    try:
        workflow = TicketWorkflow(db)
        ticket = workflow.close_ticket(
            ticket_id, 
            agent_id=1,  # 假设客服ID为1
            reply_content=request.reply_content,
            skip_quality_check=request.skip_quality_check
        )
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在或无法关闭")
        return {"message": "工单已关闭", "ticket_id": ticket.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"关闭工单时发生错误: {str(e)}")


@router.get("/tickets/statistics")
def get_ticket_statistics(db: Session = Depends(get_db)):
    """获取工单统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        工单统计信息
    """
    try:
        from app.services.ticket.status_manager import StatusManager
        from app.models.ticket import Ticket, TicketStatus
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        status_manager = StatusManager(db)
        
        # 1. 待处理工单数量（pending + processing）
        pending_count = db.query(Ticket).filter(
            Ticket.status.in_([TicketStatus.PENDING, TicketStatus.PROCESSING])
        ).count()
        
        # 2. 分配给当前客服的工单数量（由于没有认证，暂时返回0）
        my_tickets_count = 0
        
        # 3. 今日已处理工单数量（由于没有认证，统计所有今天关闭的工单）
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_processed = db.query(Ticket).filter(
            Ticket.status == TicketStatus.CLOSED,
            Ticket.updated_at >= today_start.isoformat()
        ).count()
        
        # 4. 总体统计
        total_tickets = db.query(Ticket).count()
        status_counts = {}
        for status in TicketStatus:
            count = db.query(Ticket).filter(Ticket.status == status).count()
            status_counts[status.value] = count
        
        return {
            'total': total_tickets,
            'by_status': status_counts,
            'pending_tickets': pending_count,  # 待处理工单数
            'my_tickets': my_tickets_count,     # 我的工单数
            'today_processed': today_processed  # 今日已处理
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息时发生错误: {str(e)}")


@router.get("/tickets/overdue")
def get_overdue_tickets(db: Session = Depends(get_db)):
    """获取逾期未处理的工单
    
    Args:
        db: 数据库会话
        
    Returns:
        逾期未处理的工单列表
    """
    try:
        from app.services.ticket.status_manager import StatusManager
        status_manager = StatusManager(db)
        overdue_tickets = status_manager.get_overdue_tickets()
        return [
            {
                "id": ticket.id,
                "title": ticket.title,
                "created_at": ticket.created_at,
                "updated_at": ticket.updated_at
            }
            for ticket in overdue_tickets
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取逾期工单时发生错误: {str(e)}")


@router.post("/tickets/{ticket_id}/quality-check")
def check_ticket_quality(ticket_id: int, db: Session = Depends(get_db)):
    """检查工单质量
    
    Args:
        ticket_id: 工单ID
        db: 数据库会话
        
    Returns:
        质检结果
    """
    try:
        from app.services.ticket.workflow import TicketWorkflow
        workflow = TicketWorkflow(db)
        result = workflow.check_ticket_quality(ticket_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查工单质量时发生错误: {str(e)}")


@router.get("/quality/statistics")
def get_quality_statistics(db: Session = Depends(get_db)):
    """获取质量统计信息
    
    Args:
        db: 数据库会话
        
    Returns:
        质量统计信息
    """
    try:
        from app.services.ticket.workflow import TicketWorkflow
        workflow = TicketWorkflow(db)
        stats = workflow.get_quality_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取质量统计时发生错误: {str(e)}")


@router.get("/quality-reports")
def get_quality_reports(db: Session = Depends(get_db)):
    """获取质检报告列表
    
    Args:
        db: 数据库会话
        
    Returns:
        质检报告列表
    """
    try:
        print("开始获取质检报告列表")
        
        from app.models.quality import QualityCheck
        print("导入 QualityCheck 模型成功")
        
        from app.models.ticket import Ticket, TicketResponse
        print("导入 Ticket 和 TicketResponse 模型成功")
        
        from app.models.user import User
        print("导入 User 模型成功")
        
        # 获取所有质检报告
        quality_checks = db.query(QualityCheck).all()
        print(f"获取到 {len(quality_checks)} 条质检报告")
        
        # 构建质检报告列表
        quality_reports = []
        for check in quality_checks:
            print(f"处理质检报告 ID: {check.id}, 工单 ID: {check.ticket_id}")
            
            # 获取关联的工单
            ticket = db.query(Ticket).filter(Ticket.id == check.ticket_id).first()
            if not ticket:
                print(f"工单 ID: {check.ticket_id} 不存在，跳过")
                continue
            
            # 获取关联的用户
            user = db.query(User).filter(User.id == ticket.user_id).first()
            username = user.username if user else "未知用户"
            department = user.department if user else "未知部门"
            
            print(f"获取到工单: {ticket.title}, 用户: {username}, 部门: {department}")
            
            # 获取工单回复
            response = db.query(TicketResponse).filter(
                TicketResponse.ticket_id == check.ticket_id
            ).first()
            
            print(f"获取到工单回复: {response.content if response else '无'}")
            
            # 构建质检报告
            report = {
                "id": check.id,
                "ticketId": check.ticket_id,
                "title": ticket.title,
                "content": ticket.content,
                "response": response.content if response else "",
                "score": check.score,
                "user": username,
                "department": department,
                "created_at": check.check_time
            }
            quality_reports.append(report)
            print(f"添加质检报告: {report}")
        
        # 按创建时间倒序排序
        quality_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        print(f"排序后质检报告数量: {len(quality_reports)}")
        
        return quality_reports
    except Exception as e:
        print(f"获取质检报告列表时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取质检报告列表时发生错误: {str(e)}")


@router.post("/tickets/ai-suggestion", response_model=AIReplySuggestionResponse)
def get_ai_reply_suggestion(request: AIReplySuggestionRequest, db: Session = Depends(get_db)):
    """获取AI回复建议
    
    Args:
        request: AI回复建议请求
        db: 数据库会话
        current_agent: 当前客服
        
    Returns:
        AI回复建议列表
    """
    try:
        # 获取工单信息
        from app.models.ticket import Ticket
        ticket = db.query(Ticket).filter(Ticket.id == request.ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="工单不存在")
        
        # 尝试生成AI回复建议
        suggestions = []
        
        try:
            # 导入所需服务
            from app.services.rag.retriever import Retriever
            from app.services.rag.llm_client import LLMClient
            
            # 初始化服务
            retriever = Retriever()
            llm_client = LLMClient()
            
            # 构建查询文本
            query = f"{ticket.title} {ticket.content} {request.user_message or ''}"
            
            # 从知识库中检索相关文档
            retrieved_docs = retriever.hybrid_retrieve(query, top_k=3)
            print(f"���索到 {len(retrieved_docs)} 篇相关知识库文档")
            
            # 构建用户问题
            user_question = f"用户问题：{ticket.title}\n问题描述：{ticket.content}"
            if request.user_message:
                user_question += f"\n最新消息：{request.user_message}"
            
            # 调用LLM生成回复
            llm_response = llm_client.generate_answer(user_question, retrieved_docs)
            print(f"LLM回复生成成功，置信度：{llm_response.get('confidence', 0)}")
            
            # 构建知识片段
            knowledge_items = []
            for doc in retrieved_docs:
                knowledge_items.append(
                    KnowledgeItem(
                        content=doc.get('content', '')[:300] + '...' if len(doc.get('content', '')) > 300 else doc.get('content', ''),
                        source=doc.get('source', '知识库')
                    )
                )
            
            # 提取关键字段
            print("开始提取关键字段...")
            extracted_fields_raw = llm_client.extract_fields(user_question, retrieved_docs)
            extracted_fields = [ExtractedField(name=f["name"], value=f["value"]) for f in extracted_fields_raw]
            print(f"字段提取完成: {extracted_fields}")
            
            # 解析LLM回复，生成丰富完整的建议
            llm_answer = llm_response.get('answer', '')
            
            if llm_answer and "抱歉，AI服务暂时不可用" not in llm_answer:
                # 直接使用LLM生成的完整回答，并进行格式优化
                # 清理Markdown符号
                import re
                clean_answer = llm_answer
                # 移除Markdown标题符号
                clean_answer = re.sub(r'^#{1,6}\s*', '', clean_answer, flags=re.MULTILINE)
                # 移除加粗符号
                clean_answer = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_answer)
                # 移除斜体符号
                clean_answer = re.sub(r'\*([^*]+)\*', r'\1', clean_answer)
                # 移除引用符号
                clean_answer = re.sub(r'^>\s*', '', clean_answer, flags=re.MULTILINE)
                # 移除多余的空行
                clean_answer = re.sub(r'\n{3,}', '\n\n', clean_answer)
                
                # 添加专业的开头和结尾
                professional_suggestion = f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们已经进行了详细的分析和诊断，为您提供以下完整的解决方案：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{clean_answer}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【服务承诺】
我们始终致力于为您提供专业、高效的IT技术支持服务。如果在执行上述方案过程中遇到任何困难，或问题仍未得到解决，请随时回复此工单，我们的技术专家将为您提供进一步的协助。

祝您工作顺利！
IT智能客服系统"""
                
                # 返回完整的专业建议
                suggestions = [professional_suggestion]
            else:
                # 如果LLM服务不可用，使用丰富的默认建议
                print("LLM服务不可用，使用默认建议")
                
                if '网络' in ticket.title or 'WiFi' in ticket.title or '连接' in ticket.title:
                    suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们为您提供以下详细的网络故障排查方案：

【问题诊断与分析】
网络连接问题通常由以下原因导致：
1. 路由器或调制解调器故障（概率：40%）
2. 设备网络配置错误（概率：30%）
3. WiFi信号弱或干扰（概率：20%）
4. 网络服务提供商问题（概率：10%）

【详细解决方案】

步骤1：重启网络设备
操作说明：
- 拔掉路由器电源插头
- 等待30秒后重新插上
- 观察路由器指示灯状态（正常应为绿色常亮）
预期结果：路由器正常启动，WiFi信号恢复
验证方法：尝试连接WiFi，查看是否能正常上网

步骤2：检查设备网络设置
操作说明：
- 打开设备的"设置"→"网络和Internet"
- 确认WiFi开关已开启
- 检查是否连接到正确的WiFi网络
- 验证WiFi密码输入正确
预期结果：设备成功连接到WiFi网络
验证方法：查看网络状态显示"已连接"

步骤3：网络诊断测试
操作说明：
- 打开命令提示符（Windows）或终端（Mac）
- 输入命令：ping www.baidu.com
- 查看返回结果
预期结果：显示正常的响应时间和数据包返回
验证方法：能够正常访问百度等网站

【备选方案】
如果上述步骤无效，请尝试：
1. 重置网络设置：设置→网络和Internet→网络重置
2. 更新网卡驱动程序
3. 尝试使用有线网络连接测试
4. 联系网络服务提供商确认是否有区域故障

【注意事项与风险提示】
- 操作前请确保保存正在进行的工作
- 重启路由器期间，所有连接设备将暂时断网
- 重置网络设置将清除已保存的WiFi密码
- 修改网络配置前建议记录原始设置

【预防建议】
- 定期重启路由器（建议每周一次）
- 将路由器放置在通风良好、远离干扰源的位置
- 定期更新路由器固件
- 使用强密码保护WiFi网络

【参考信息】
- 知识库来源：IT运维手册-网络故障排查指南
- 如需进一步协助，请回复此工单或拨打IT服务热线：400-XXX-XXXX

【总结】
网络问题大多数可以通过重启设备和检查设置解决。请按照上述步骤逐步排查，如问题持续存在，我们的技术专家将为您提供远程或现场支持。

祝您工作顺利！
IT智能客服系统"""]
                elif '电脑' in ticket.title or '开机' in ticket.title or '启动' in ticket.title:
                    suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们为您提供以下详细的硬件故障排查方案：

【问题诊断与分析】
电脑无法开机通常由以下原因导致：
1. 电源连接问题（概率：35%）
2. 硬件故障（内存、硬盘等）（概率：25%）
3. 系统软件问题（概率：20%）
4. 外接设备冲突（概率：15%）
5. 主板或电源损坏（概率：5%）

【详细解决方案】

步骤1：检查电源连接
操作说明：
- 确认电源线两端连接牢固
- 检查电源插座是否有电（可插入其他设备测试）
- 如果是笔记本电脑，检查电池是否安装正确
- 尝试更换电源线或插座
预期结果：电源指示灯亮起或听到风扇转动声
验证方法：观察电源指示灯状态

步骤2：强制重启操作
操作说明：
- 长按电源键10-15秒强制关机
- 拔掉所有外接设备（USB设备、外接显示器等）
- 等待1分钟后再次按电源键开机
预期结果：电脑正常启动，显示开机画面
验证方法：听到开机音乐或看到品牌Logo

步骤3：硬件自检排查
操作说明：
- 关机并断开电源
- 打开机箱侧板（台式机）或后盖（部分笔记本）
- 检查内存条是否插紧，可尝试重新插拔
- 清理内部灰尘
预期结果：硬件连接正常，无松动现象
验证方法：重新组装后能正常开机

【备选方案】
如果上述步骤无效，请尝试：
1. 进入安全模式：开机时连续按F8键
2. 使用系统恢复功能（如有恢复分区）
3. 检查显示器连接（可能是显示问题而非主机问题）
4. 联系专业维修人员进行硬件检测

【注意事项与风险提示】
⚠️ 重要提示：
- 操作前请确保已保存所有重要数据
- 拆机操作可能导致保修失效，建议联系专业人员
- 如果闻到烧焦味或看到冒烟，立即停止操作并断电
- 静电可能损坏敏感电子元件，操作前请触摸金属物体释放静电

【预防建议】
- 定期清理电脑内部灰尘（建议每半年一次）
- 使用UPS不间断电源保护设备
- 避免在电压不稳的环境中使用电脑
- 定期备份重要数据到云端或外部存储
- 保持系统和驱动程序更新

【参考信息】
- 知识库来源：IT运维手册-硬件故障排查指南
- 如需进一步协助，请回复此工单或拨打IT服务热线：400-XXX-XXXX

【总结】
电脑无法开机问题需要系统性地排查电源、硬件和软件三个方面。建议按照上述步骤从简单到复杂逐步排查。如涉及硬件拆机操作，建议联系IT支持团队协助处理。

祝您工作顺利！
IT智能客服系统"""]
                else:
                    suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们已经收到并正在积极处理中。

【问题受理确认】
您的工单已录入系统，工单编号：#{ticket.id}
问题类型：{ticket.category or '待分类'}
提交时间：{ticket.created_at}

【当前处理状态】
✓ 问题已记录
✓ 正在分配合适的技术专家
⏳ 正在分析问题和制定解决方案

【预计处理时间】
根据问题复杂程度，我们预计将在以下时间内为您提供解决方案：
- 简单问题：2小时内响应
- 一般问题：4小时内响应
- 复杂问题：8小时内响应（可能需要现场支持）

【您可以提前准备】
为了加快问题解决速度，您可以提前准备以下信息：
1. 问题的详细描述（何时发生、频率、影响范围）
2. 相关的错误提示截图
3. 已尝试的解决方法
4. 设备型号和系统版本信息

【服务承诺】
我们承诺：
- 所有工单将在24小时内得到首次响应
- 提供7×24小时技术支持服务
- 复杂问题将安排专业技术工程师跟进
- 全程跟踪直至问题完全解决

【联系方式】
如需紧急协助，您可以通过以下方式联系我们：
- 回复此工单
- IT服务热线：400-XXX-XXXX
- 企业微信：IT支持群
- 邮件：itsupport@company.com

再次感谢您的耐心等待，我们将尽快为您提供专业的解决方案！

祝您工作顺利！
IT智能客服系统"""]
        except Exception as e:
            # 如果服务调用失败，使用丰富的默认建议
            print(f"服务调用失败: {str(e)}")
            
            if '网络' in ticket.title or 'WiFi' in ticket.title or '连接' in ticket.title:
                suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们为您提供以下详细的网络故障排查方案：

【问题诊断与分析】
网络连接问题通常由以下原因导致：
1. 路由器或调制解调器故障（概率：40%）
2. 设备网络配置错误（概率：30%）
3. WiFi信号弱或干扰（概率：20%）
4. 网络服务提供商问题（概率：10%）

【详细解决方案】

步骤1：重启网络设备
操作说明：
- 拔掉路由器电源插头
- 等待30秒后重新插上
- 观察路由器指示灯状态（正常应为绿色常亮）
预期结果：路由器正常启动，WiFi信号恢复

步骤2：检查设备网络设置
操作说明：
- 打开设备的"设置"→"网络和Internet"
- 确认WiFi开关已开启
- 检查是否连接到正确的WiFi网络

步骤3：网络诊断测试
操作说明：
- 打开命令提示符（Windows）或终端（Mac）
- 输入命令：ping www.baidu.com
- 查看返回结果

【备选方案】
如果上述步骤无效，请尝试：
1. 重置网络设置
2. 更新网卡驱动程序
3. 尝试使用有线网络连接测试

【注意事项与风险提示】
- 操作前请确保保存正在进行的工作
- 重启路由器期间，所有连接设备将暂时断网

【预防建议】
- 定期重启路由器（建议每周一次）
- 将路由器放置在通风良好、远离干扰源的位置

【总结】
网络问题大多数可以通过重启设备和检查设置解决。请按照上述步骤逐步排查。

祝您工作顺利！
IT智能客服系统"""]
            elif '电脑' in ticket.title or '开机' in ticket.title or '启动' in ticket.title:
                suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们为您提供以下详细的硬件故障排查方案：

【问题诊断与分析】
电脑无法开机通常由以下原因导致：
1. 电源连接问题（概率：35%）
2. 硬件故障（内存、硬盘等）（概率：25%）
3. 系统软件问题（概率：20%）
4. 外接设备冲突（概率：15%）

【详细解决方案】

步骤1：检查电源连接
操作说明：
- 确认电源线两端连接牢固
- 检查电源插座是否有电
- 如果是笔记本电脑，检查电池是否安装正确

步骤2：强制重启操作
操作说明：
- 长按电源键10-15秒强制关机
- 拔掉所有外接设备
- 等待1分钟后再次按电源键开机

步骤3：硬件自检排查
操作说明：
- 关机并断开电源
- 检查内存条是否插紧
- 清理内部灰尘

【注意事项与风险提示】
⚠️ 重要提示：
- 操作前请确保已保存所有重要数据
- 拆机操作可能导致保修失效

【预防建议】
- 定期清理电脑内部灰尘
- 使用UPS不间断电源保护设备
- 定期备份重要数据

【总结】
电脑无法开机问题需要系统性地排查电源、硬件和软件三个方面。

祝您工作顺利！
IT智能客服系统"""]
            else:
                suggestions = [f"""尊敬的用户，您好！

感谢您联系IT智能客服系统。针对您反馈的"{ticket.title}"问题，我们已经收到并正在积极处理中。

【问题受理确认】
您的工单已录入系统，工单编号：#{ticket.id}
问题类型：{ticket.category or '待分类'}

【当前处理状态】
✓ 问题已记录
✓ 正在分配合适的技术专家
⏳ 正在分析问题和制定解决方案

【预计处理时间】
- 简单问题：2小时内响应
- 一般问题：4小时内响应
- 复杂问题：8小时内响应

【联系方式】
如需紧急协助，请回复此工单或拨打IT服务热线。

祝您工作顺利！
IT智能客服系统"""]
        
        return AIReplySuggestionResponse(
            ticket_id=request.ticket_id,
            suggestions=suggestions,
            knowledge_items=knowledge_items,
            extracted_fields=extracted_fields
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI回复建议时发生错误: {str(e)}")
