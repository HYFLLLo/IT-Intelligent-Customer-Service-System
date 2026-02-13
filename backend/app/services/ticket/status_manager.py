from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ...models.ticket import Ticket, TicketStatus

class StatusManager:
    def __init__(self, db: Session):
        self.db = db
    
    def update_status(self, ticket_id: int, new_status: TicketStatus, user_id: int) -> Optional[Ticket]:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None
        
        if not self._is_valid_status_transition(ticket.status, new_status):
            return None
        
        ticket.status = new_status
        ticket.updated_at = datetime.now().isoformat()
        
        if new_status == TicketStatus.PROCESSING and not ticket.assigned_agent_id:
            ticket.assigned_agent_id = user_id
        
        self.db.commit()
        self.db.refresh(ticket)
        
        return ticket
    
    def _is_valid_status_transition(self, current_status: TicketStatus, new_status: TicketStatus) -> bool:
        valid_transitions = {
            TicketStatus.PENDING: [TicketStatus.PROCESSING, TicketStatus.CLOSED],
            TicketStatus.PROCESSING: [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.PENDING],
            TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.REOPENED],
            TicketStatus.CLOSED: [TicketStatus.REOPENED],
            TicketStatus.REOPENED: [TicketStatus.PROCESSING, TicketStatus.CLOSED]
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def get_tickets_by_status(self, status: TicketStatus) -> list[Ticket]:
        return self.db.query(Ticket).filter(Ticket.status == status).all()
    
    def get_tickets_by_agent(self, agent_id: int, status: TicketStatus = None, source=None) -> list[Ticket]:
        query = self.db.query(Ticket).filter(Ticket.assigned_agent_id == agent_id)
        if status:
            query = query.filter(Ticket.status == status)
        if source:
            query = query.filter(Ticket.source == source)
        return query.all()
    
    def get_tickets_by_user(self, user_id: int, status: TicketStatus = None) -> list[Ticket]:
        query = self.db.query(Ticket).filter(Ticket.user_id == user_id)
        if status:
            query = query.filter(Ticket.status == status)
        return query.all()
    
    def get_overdue_tickets(self, hours_threshold: int = 24) -> list[Ticket]:
        from datetime import datetime, timedelta
        
        threshold_time = datetime.now() - timedelta(hours=hours_threshold)
        threshold_iso = threshold_time.isoformat()
        
        overdue_tickets = self.db.query(Ticket).filter(
            Ticket.status.in_([TicketStatus.PENDING, TicketStatus.PROCESSING, TicketStatus.REOPENED]),
            Ticket.updated_at < threshold_iso
        ).all()
        
        return overdue_tickets
    
    def get_ticket_statistics(self) -> dict:
        total_tickets = self.db.query(Ticket).count()
        status_counts = {}
        
        for status in TicketStatus:
            count = self.db.query(Ticket).filter(Ticket.status == status).count()
            status_counts[status.value] = count
        
        return {
            'total': total_tickets,
            'by_status': status_counts
        }
    
    def escalate_ticket(self, ticket_id: int, reason: str) -> Optional[Ticket]:
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None
        
        from ...models.ticket import TicketPriority
        
        priority_order = [TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH, TicketPriority.URGENT]
        current_index = priority_order.index(ticket.priority)
        
        if current_index < len(priority_order) - 1:
            ticket.priority = priority_order[current_index + 1]
            ticket.updated_at = datetime.now().isoformat()
            self.db.commit()
            self.db.refresh(ticket)
        
        return ticket