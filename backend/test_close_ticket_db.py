from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ticket.workflow import TicketWorkflow
from app.models.ticket import Ticket, TicketStatus

# 直接测试数据库操作
def test_close_ticket_db():
    print("=== 测试关闭工单数据库操作 ===")
    
    # 获取数据库会话
    db: Session = next(get_db())
    
    try:
        # 查找一个状态为PROCESSING的工单
        ticket = db.query(Ticket).filter(Ticket.status == TicketStatus.PROCESSING).first()
        
        if not ticket:
            # 如果没有PROCESSING状态的工单，查找PENDING状态的
            ticket = db.query(Ticket).filter(Ticket.status == TicketStatus.PENDING).first()
        
        if not ticket:
            print("❌ 没有找到可测试的工单")
            return
        
        print(f"找到测试工单:")
        print(f"   ID: {ticket.id}")
        print(f"   标题: {ticket.title}")
        print(f"   状态: {ticket.status.value}")
        
        # 创建Workflow实例
        workflow = TicketWorkflow(db)
        
        # 测试关闭工单
        test_reply_content = "问题已解决，请重启设备后验证。如果仍有问题，请随时联系我们。"
        
        print("\n测试关闭工单...")
        
        # 执行关闭操作
        closed_ticket = workflow.close_ticket(
            ticket_id=ticket.id,
            agent_id=1,  # 假设客服ID为1
            reply_content=test_reply_content,
            skip_quality_check=True  # 跳过质量检查以简化测试
        )
        
        if closed_ticket:
            print(f"✅ 关闭工单成功:")
            print(f"   工单ID: {closed_ticket.id}")
            print(f"   新状态: {closed_ticket.status.value}")
            print(f"   解决时间: {closed_ticket.resolved_at}")
            
            # 检查是否创建了回复记录
            from app.models.ticket import TicketResponse
            response = db.query(TicketResponse).filter(
                TicketResponse.ticket_id == ticket.id,
                TicketResponse.agent_id == 1
            ).order_by(TicketResponse.created_at.desc()).first()
            
            if response:
                print(f"✅ 回复记录已创建:")
                print(f"   回复内容: {response.content[:50]}...")
            else:
                print(f"❌ 回复记录未创建")
        else:
            print(f"❌ 关闭工单失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    finally:
        # 关闭数据库会话
        db.close()

if __name__ == "__main__":
    test_close_ticket_db()
    print("\n=== 测试完成 ===")
