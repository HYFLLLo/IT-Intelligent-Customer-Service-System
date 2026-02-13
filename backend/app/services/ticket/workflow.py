from datetime import datetime
from sqlalchemy.orm import Session
from ...models.ticket import Ticket, TicketStatus
from ...models.user import User
from .field_extractor import FieldExtractor
from .ai_field_extractor import AIFieldExtractor
from .ai_quality_checker import AIQualityChecker
from .agent_assigner import AgentAssigner
from .status_manager import StatusManager

class TicketWorkflow:
    def __init__(self, db: Session):
        self.db = db
        self.field_extractor = FieldExtractor()
        self.ai_field_extractor = AIFieldExtractor()
        self.ai_quality_checker = AIQualityChecker(db)
        self.agent_assigner = AgentAssigner(db)
        self.status_manager = StatusManager(db)
    
    def create_ticket(self, title: str, content: str, user_id: int, priority: str = None, category: str = None, source: str = None) -> Ticket:
        
        # 对于转人工或员工主动创建的工单，跳过AI字段提取以提高速度
        # 但保留用户设置的优先级和分类
        from ...models.ticket import TicketPriority
        if source and (source.lower() == 'transferred' or source.lower() == 'employee_created'):
            # 使用简单的字段提取器，避免调用AI
            # 优先使用用户传入的优先级，如果没有则使用默认值
            extracted_fields = {
                'priority': None,  # 后面会根据priority参数处理
                'category': category  # 直接使用用户传入的分类
            }
        else:
            extracted_fields = self.ai_field_extractor.extract_fields(content)
        
        # 确保优先级值有效
        # 优先使用用户设置的优先级
        from ...models.ticket import TicketPriority, TicketSource
        
        # 将用户设置的优先级转换为枚举
        priority_map = {
            'low': TicketPriority.LOW,
            'medium': TicketPriority.MEDIUM,
            'high': TicketPriority.HIGH,
            'urgent': TicketPriority.URGENT,
            # 添加中文映射
            '紧急': TicketPriority.URGENT,
            '高': TicketPriority.HIGH,
            '中': TicketPriority.MEDIUM,
            '低': TicketPriority.LOW
        }
        
        if priority and isinstance(priority, str):
            # 用户传入了字符串类型的优先级
            priority_str = priority.lower()
            if priority_str in priority_map:
                priority = priority_map[priority_str]
            else:
                # 如果用户设置的优先级无效，使用提取的优先级或默认值
                priority = extracted_fields.get('priority') or TicketPriority.MEDIUM
        elif priority is None:
            # 如果用户没有设置优先级，使用提取的优先级或默认值
            priority = extracted_fields.get('priority') or TicketPriority.MEDIUM
        # 如果priority已经是枚举类型，保持不变
        
        # 优先使用用户设置的分类
        if not category:
            category = extracted_fields.get('category')
        
        # 处理工单来源
        ticket_source = TicketSource.TRANSFERRED  # 默认是转人工
        if source:
            source_str = source.lower()
            if source_str == 'employee_created' or source_str == 'employee':
                ticket_source = TicketSource.EMPLOYEE_CREATED
        
        ticket = Ticket(
            title=title,
            content=content,
            status=TicketStatus.PENDING,
            priority=priority,
            source=ticket_source,
            user_id=user_id,
            category=category,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        
        assigned_agent = self.agent_assigner.assign_agent(ticket.id)
        if assigned_agent:
            ticket.assigned_agent_id = assigned_agent.id
            ticket.status = TicketStatus.PROCESSING
            ticket.updated_at = datetime.now().isoformat()
            self.db.commit()
            self.db.refresh(ticket)
        
        return ticket
    
    def process_ticket(self, ticket_id: int, agent_id: int) -> Ticket:
        return self.status_manager.update_status(ticket_id, TicketStatus.PROCESSING, agent_id)
    
    def resolve_ticket(self, ticket_id: int, agent_id: int, resolution: str) -> Ticket:
        return self.status_manager.update_status(ticket_id, TicketStatus.RESOLVED, agent_id)
    
    def close_ticket(self, ticket_id: int, agent_id: int, reply_content: str = None, skip_quality_check: bool = False) -> Ticket:
        ticket = self.status_manager.update_status(ticket_id, TicketStatus.CLOSED, agent_id)
        if ticket:
            ticket.resolved_at = datetime.now().isoformat()
            
            # 记录客服回复
            if reply_content:
                from ...models.ticket import TicketResponse
                ticket_response = TicketResponse(
                    ticket_id=ticket.id,
                    agent_id=agent_id,
                    content=reply_content,
                    created_at=datetime.now().isoformat()
                )
                self.db.add(ticket_response)
            
            self.db.commit()
            self.db.refresh(ticket)
        
        # 进行质量检查
        if not skip_quality_check:
            quality_result = self.check_ticket_quality(ticket_id)
            if quality_result and quality_result.get('score', 0) < 3.0:
                # 质量评分低于3.0，记录警告
                print(f"警告：工单 #{ticket_id} 质量评分较低: {quality_result.get('score', 0)}")
        return ticket
    
    def reopen_ticket(self, ticket_id: int, user_id: int) -> Ticket:
        return self.status_manager.update_status(ticket_id, TicketStatus.REOPENED, user_id)
    
    def get_ticket_by_id(self, ticket_id: int) -> Ticket:
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    def get_tickets_by_status(self, status: TicketStatus) -> list[Ticket]:
        return self.db.query(Ticket).filter(Ticket.status == status).all()
    
    def get_tickets_by_agent(self, agent_id: int) -> list[Ticket]:
        return self.db.query(Ticket).filter(Ticket.assigned_agent_id == agent_id).all()
    
    def check_ticket_quality(self, ticket_id: int) -> dict:
        """检查工单质量
        
        Args:
            ticket_id: 工单ID
            
        Returns:
            质检结果
        """
        return self.ai_quality_checker.check_ticket_quality(ticket_id)
    
    def resolve_ticket_with_quality_check(self, ticket_id: int, agent_id: int, resolution: str) -> dict:
        """解决工单并进行质量检查
        
        Args:
            ticket_id: 工单ID
            agent_id: 客服ID
            resolution: 解决方案
            
        Returns:
            包含工单和质检结果的字典
        """
        ticket = self.resolve_ticket(ticket_id, agent_id, resolution)
        if ticket:
            quality_result = self.check_ticket_quality(ticket_id)
            return {
                "ticket": ticket,
                "quality_check": quality_result
            }
        return {"ticket": ticket, "quality_check": None}
    
    def get_quality_statistics(self) -> dict:
        """获取质量统计信息
        
        Returns:
            质量统计信息
        """
        return self.ai_quality_checker.get_quality_statistics()