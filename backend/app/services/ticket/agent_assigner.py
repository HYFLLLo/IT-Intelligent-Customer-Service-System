from sqlalchemy.orm import Session
from typing import Optional
from ...models.user import User, UserRole
from ...models.ticket import Ticket, TicketStatus

class AgentAssigner:
    def __init__(self, db: Session):
        self.db = db
    
    def assign_agent(self, ticket_id: int) -> Optional[User]:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None
        
        available_agents = self._get_available_agents()
        if not available_agents:
            return None
        
        if ticket.category:
            specialized_agents = self._get_specialized_agents(ticket.category, available_agents)
            if specialized_agents:
                return self._select_best_agent(specialized_agents, ticket.priority)
        
        return self._select_best_agent(available_agents, ticket.priority)
    
    def _get_available_agents(self) -> list[User]:
        return self.db.query(User).filter(User.role == UserRole.AGENT).all()
    
    def _get_specialized_agents(self, category: str, available_agents: list[User]) -> list[User]:
        
        category_expertise = {
            'technical': ['技术', '技术支持', '技术客服', 'technical', 'tech support'],
            'billing': ['财务', ' billing', '计费', '财务客服', 'finance', 'accounting'],
            'account': ['账户', '账号', '会员', 'account', 'member services'],
            'support': ['支持', '客服', 'customer support', '服务']
        }
        
        expertise_keywords = category_expertise.get(category, [])
        
        specialized_agents = []
        for agent in available_agents:
            if agent.department:
                dept_lower = agent.department.lower()
                for keyword in expertise_keywords:
                    if keyword.lower() in dept_lower:
                        specialized_agents.append(agent)
                        break
        
        return specialized_agents if specialized_agents else available_agents
    
    def _select_best_agent(self, agents: list[User], priority) -> Optional[User]:
        agent_scores = {}
        
        for agent in agents:
            workload = self._get_agent_workload(agent.id)
            expertise_score = self._get_expertise_score(agent, priority)
            
            score = (100 - workload * 10) + expertise_score * 20
            agent_scores[agent] = score
        
        if agent_scores:
            return max(agent_scores, key=agent_scores.get)
        
        return None
    
    def _get_agent_workload(self, agent_id: int) -> int:
        active_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_agent_id == agent_id,
            Ticket.status.in_([TicketStatus.PENDING, TicketStatus.PROCESSING, TicketStatus.REOPENED])
        ).count()
        return min(active_tickets, 10)
    
    def _get_expertise_score(self, agent: User, priority) -> int:
        
        if agent.department:
            dept = agent.department.lower()
            # 处理TicketPriority枚举对象
            priority_str = str(priority).lower() if priority else ''
            if 'urgent' in priority_str:
                if any(keyword in dept for keyword in ['技术', 'technical', '紧急', 'urgent']):
                    return 5
            elif 'high' in priority_str:
                if any(keyword in dept for keyword in ['技术', 'technical', '重要', 'important']):
                    return 4
        
        return 3
    
    def reassign_agent(self, ticket_id: int, current_agent_id: int) -> Optional[User]:
        
        available_agents = [agent for agent in self._get_available_agents() if agent.id != current_agent_id]
        if not available_agents:
            return None
        
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None
        
        if ticket.category:
            specialized_agents = self._get_specialized_agents(ticket.category, available_agents)
            if specialized_agents:
                return self._select_best_agent(specialized_agents, ticket.priority)
        
        return self._select_best_agent(available_agents, ticket.priority)