from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth.auth_dependency import get_current_admin, get_current_active_user
from app.models.user import User, UserRole
from app.models.knowledge import KnowledgeDocument, KnowledgeCategory
from app.models.quality import QualityRule
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class KnowledgeCreate(BaseModel):
    """知识库创建模型"""
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    is_active: bool = True


class KnowledgeUpdate(BaseModel):
    """知识库更新模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class KnowledgeResponse(BaseModel):
    """知识库响应模型"""
    id: int
    title: str
    content: str
    category: str
    tags: Optional[List[str]] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    role: str
    department: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class QualityRuleCreate(BaseModel):
    """质检规则创建模型"""
    name: str
    description: str
    criteria: List[dict]
    weight: float = 1.0
    is_active: bool = True


class QualityRuleUpdate(BaseModel):
    """质检规则更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    criteria: Optional[List[dict]] = None
    weight: Optional[float] = None
    is_active: Optional[bool] = None


class QualityRuleResponse(BaseModel):
    """质检规则响应模型"""
    id: int
    name: str
    description: str
    criteria: List[dict]
    weight: float
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """仪表盘统计模型"""
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    closed_tickets: int
    average_resolution_time: float
    agent_performance: List[dict]
    category_distribution: List[dict]


# 知识库管理
@router.post("/knowledge", response_model=KnowledgeResponse)
def create_knowledge(knowledge: KnowledgeCreate, db: Session = Depends(get_db)):
    """创建知识库条目
    
    Args:
        knowledge: 知识库创建信息
        db: 数据库会话
        
    Returns:
        创建的知识库条目
    """
    try:
        from app.services.rag.document_processor import DocumentProcessor
        from datetime import datetime
        
        # 查找或创建分类
        category = db.query(KnowledgeCategory).filter(KnowledgeCategory.name == knowledge.category).first()
        if not category:
            category = KnowledgeCategory(
                name=knowledge.category,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            db.add(category)
            db.commit()
            db.refresh(category)
        
        # 创建知识库条目
        new_knowledge = KnowledgeDocument(
            category_id=category.id,
            title=knowledge.title,
            content=knowledge.content,
            source="admin",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(new_knowledge)
        db.commit()
        db.refresh(new_knowledge)
        
        # 更新向量数据库
        processor = DocumentProcessor()
        processor.add_document(
            document_id=str(new_knowledge.id),
            content=knowledge.content,
            metadata={
                "title": knowledge.title,
                "category": knowledge.category,
                "tags": knowledge.tags
            }
        )
        
        return KnowledgeResponse(
            id=new_knowledge.id,
            title=new_knowledge.title,
            content=new_knowledge.content,
            category=category.name,
            tags=knowledge.tags,
            is_active=True,
            created_at=new_knowledge.created_at,
            updated_at=new_knowledge.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建知识库条目时发生错误: {str(e)}")


@router.get("/knowledge", response_model=List[KnowledgeResponse])
def get_knowledge_list(
    category: Optional[str] = Query(None, description="按分类筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db)
):
    """获取知识库列表
    
    Args:
        category: 分类筛选
        is_active: 状态筛选
        db: 数据库会话
        
    Returns:
        知识库列表
    """
    try:
        query = db.query(KnowledgeDocument)
        
        if category:
            # 先查找分类ID
            category_obj = db.query(KnowledgeCategory).filter(KnowledgeCategory.name == category).first()
            if category_obj:
                query = query.filter(KnowledgeDocument.category_id == category_obj.id)
        if is_active is not None:
            query = query.filter(KnowledgeDocument.is_active == is_active)
        
        knowledge_list = query.all()
        
        result = []
        for item in knowledge_list:
            # 获取分类名称
            category_obj = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == item.category_id).first()
            category_name = category_obj.name if category_obj else ""
            
            result.append(
                KnowledgeResponse(
                    id=item.id,
                    title=item.title,
                    content=item.content,
                    category=category_name,
                    tags=[],
                    is_active=True,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
            )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库列表时发生错误: {str(e)}")


@router.get("/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
def get_knowledge_detail(knowledge_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """获取知识库详情
    
    Args:
        knowledge_id: 知识库ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        知识库详情
    """
    try:
        knowledge = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == knowledge_id).first()
        if not knowledge:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
        
        # 获取分类名称
        category_obj = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == knowledge.category_id).first()
        category_name = category_obj.name if category_obj else ""
        
        return KnowledgeResponse(
            id=knowledge.id,
            title=knowledge.title,
            content=knowledge.content,
            category=category_name,
            tags=knowledge.tags,
            is_active=knowledge.is_active,
            created_at=knowledge.created_at,
            updated_at=knowledge.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取知识库详情时发生错误: {str(e)}")


@router.put("/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
def update_knowledge(knowledge_id: int, knowledge: KnowledgeUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """更新知识库条目
    
    Args:
        knowledge_id: 知识库ID
        knowledge: 知识库更新信息
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的知识库条目
    """
    try:
        existing_knowledge = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == knowledge_id).first()
        if not existing_knowledge:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
        
        # 更新字段
        update_data = knowledge.model_dump(exclude_unset=True)
        category_name = ""
        
        for field, value in update_data.items():
            if field == "category" and value:
                # 查找或创建分类
                category = db.query(KnowledgeCategory).filter(KnowledgeCategory.name == value).first()
                if not category:
                    category = KnowledgeCategory(
                        name=value,
                        created_at=datetime.utcnow().isoformat(),
                        updated_at=datetime.utcnow().isoformat()
                    )
                    db.add(category)
                    db.commit()
                    db.refresh(category)
                existing_knowledge.category_id = category.id
                category_name = value
            else:
                setattr(existing_knowledge, field, value)
        
        db.commit()
        db.refresh(existing_knowledge)
        
        # 获取分类名称
        if not category_name:
            category_obj = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == existing_knowledge.category_id).first()
            category_name = category_obj.name if category_obj else ""
        
        # 更新向量数据库
        from app.services.rag.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        processor.update_document(
            document_id=str(knowledge_id),
            content=existing_knowledge.content,
            metadata={
                "title": existing_knowledge.title,
                "category": category_name
            }
        )
        
        return KnowledgeResponse(
            id=existing_knowledge.id,
            title=existing_knowledge.title,
            content=existing_knowledge.content,
            category=category_name,
            tags=existing_knowledge.tags,
            is_active=existing_knowledge.is_active,
            created_at=existing_knowledge.created_at,
            updated_at=existing_knowledge.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新知识库条目时发生错误: {str(e)}")


@router.delete("/knowledge/{knowledge_id}")
def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    """删除知识库条目
    
    Args:
        knowledge_id: 知识库ID
        db: 数据库会话
        
    Returns:
        操作结果
    """
    try:
        existing_knowledge = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == knowledge_id).first()
        if not existing_knowledge:
            raise HTTPException(status_code=404, detail="知识库条目不存在")
        
        # 从向量数据库中删除
        try:
            from app.services.rag.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            processor.delete_document(document_id=str(knowledge_id))
        except Exception as e:
            print(f"从向量数据库删除失败（可能文档不存在）: {e}")
        
        # 从数据库中删除
        db.delete(existing_knowledge)
        db.commit()
        
        return {"message": "知识库条目已删除", "knowledge_id": knowledge_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除知识库条目时发生错误: {str(e)}")


# 权限配置
@router.get("/users", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = Query(None, description="按角色筛选"),
    department: Optional[str] = Query(None, description="按部门筛选"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取用户列表
    
    Args:
        role: 角色筛选
        department: 部门筛选
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        用户列表
    """
    try:
        query = db.query(User)
        
        if role:
            query = query.filter(User.role == UserRole(role))
        if department:
            query = query.filter(User.department == department)
        
        users = query.all()
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role.value,
                department=user.department,
                created_at=user.created_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表时发生错误: {str(e)}")


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """获取用户详情
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        用户详情
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            department=user.department,
            created_at=user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户详情时发生错误: {str(e)}")


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """更新用户信息
    
    Args:
        user_id: 用户ID
        user_update: 用户更新信息
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的用户信息
    """
    try:
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新字段
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "role" and value:
                setattr(existing_user, field, UserRole(value))
            else:
                setattr(existing_user, field, value)
        
        db.commit()
        db.refresh(existing_user)
        
        return UserResponse(
            id=existing_user.id,
            username=existing_user.username,
            email=existing_user.email,
            role=existing_user.role.value,
            department=existing_user.department,
            created_at=existing_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新用户信息时发生错误: {str(e)}")


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """删除用户
    
    Args:
        user_id: 用户ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        existing_user = db.query(User).filter(User.id == user_id).first()
        if not existing_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不允许删除自己
        if existing_user.id == current_admin.id:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")
        
        db.delete(existing_user)
        db.commit()
        
        return {"message": "用户已删除", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除用户时发生错误: {str(e)}")


# 质检规则设置
@router.post("/quality-rules", response_model=QualityRuleResponse)
def create_quality_rule(rule: QualityRuleCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """创建质检规则
    
    Args:
        rule: 质检规则创建信息
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        创建的质检规则
    """
    try:
        new_rule = QualityRule(
            rule_name=rule.name,
            description=rule.description,
            weight=str(rule.weight),
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        db.add(new_rule)
        db.commit()
        db.refresh(new_rule)
        
        return QualityRuleResponse(
            id=new_rule.id,
            name=new_rule.rule_name,
            description=new_rule.description,
            criteria=[],
            weight=float(new_rule.weight) if new_rule.weight else 1.0,
            is_active=True,
            created_at=new_rule.created_at,
            updated_at=new_rule.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建质检规则时发生错误: {str(e)}")


@router.get("/quality-rules", response_model=List[QualityRuleResponse])
def get_quality_rules(
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取质检规则列表
    
    Args:
        is_active: 状态筛选
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        质检规则列表
    """
    try:
        query = db.query(QualityRule)
        
        # 由于数据库模型中没有is_active字段，暂时忽略此筛选
        # if is_active is not None:
        #     query = query.filter(QualityRule.is_active == is_active)
        
        rules = query.all()
        
        return [
            QualityRuleResponse(
                id=rule.id,
                name=rule.rule_name,
                description=rule.description,
                criteria=[],
                weight=float(rule.weight) if rule.weight else 1.0,
                is_active=True,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            for rule in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取质检规则列表时发生错误: {str(e)}")


@router.put("/quality-rules/{rule_id}", response_model=QualityRuleResponse)
def update_quality_rule(rule_id: int, rule_update: QualityRuleUpdate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """更新质检规则
    
    Args:
        rule_id: 质检规则ID
        rule_update: 质检规则更新信息
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        更新后的质检规则
    """
    try:
        existing_rule = db.query(QualityRule).filter(QualityRule.id == rule_id).first()
        if not existing_rule:
            raise HTTPException(status_code=404, detail="质检规则不存在")
        
        # 更新字段
        update_data = rule_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "name":
                setattr(existing_rule, "rule_name", value)
            elif field == "weight":
                setattr(existing_rule, "weight", str(value))
            elif field not in ["criteria", "is_active"]:  # 忽略数据库模型中不存在的字段
                setattr(existing_rule, field, value)
        
        # 更新时间戳
        existing_rule.updated_at = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(existing_rule)
        
        return QualityRuleResponse(
            id=existing_rule.id,
            name=existing_rule.rule_name,
            description=existing_rule.description,
            criteria=[],
            weight=float(existing_rule.weight) if existing_rule.weight else 1.0,
            is_active=True,
            created_at=existing_rule.created_at,
            updated_at=existing_rule.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新质检规则时发生错误: {str(e)}")


@router.delete("/quality-rules/{rule_id}")
def delete_quality_rule(rule_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """删除质检规则
    
    Args:
        rule_id: 质检规则ID
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        操作结果
    """
    try:
        existing_rule = db.query(QualityRule).filter(QualityRule.id == rule_id).first()
        if not existing_rule:
            raise HTTPException(status_code=404, detail="质检规则不存在")
        
        db.delete(existing_rule)
        db.commit()
        
        return {"message": "质检规则已删除", "rule_id": rule_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除质检规则时发生错误: {str(e)}")


# 数据看板
@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_admin: User = Depends(get_current_admin)):
    """获取仪表盘统计信息
    
    Args:
        db: 数据库会话
        current_admin: 当前管理员
        
    Returns:
        仪表盘统计信息
    """
    try:
        from app.models.ticket import Ticket, TicketStatus
        from sqlalchemy import func
        from datetime import datetime
        
        # 总工单数
        total_tickets = db.query(func.count(Ticket.id)).scalar() or 0
        
        # 开放工单数
        open_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == TicketStatus.OPEN).scalar() or 0
        
        # 已解决工单数
        resolved_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == TicketStatus.RESOLVED).scalar() or 0
        
        # 已关闭工单数
        closed_tickets = db.query(func.count(Ticket.id)).filter(Ticket.status == TicketStatus.CLOSED).scalar() or 0
        
        # 平均解决时间
        resolved_tickets_query = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED).all()
        if resolved_tickets_query:
            total_time = 0
            for ticket in resolved_tickets_query:
                if ticket.resolved_at and ticket.created_at:
                    created_at = datetime.fromisoformat(ticket.created_at)
                    resolved_at = datetime.fromisoformat(ticket.resolved_at)
                    total_time += (resolved_at - created_at).total_seconds() / 3600  # 转换为小时
            average_resolution_time = total_time / len(resolved_tickets_query) if resolved_tickets_query else 0
        else:
            average_resolution_time = 0
        
        # 客服绩效
        agent_performance = []
        agents = db.query(User).filter(User.role == UserRole.AGENT).all()
        for agent in agents:
            assigned_tickets = db.query(func.count(Ticket.id)).filter(Ticket.assigned_agent_id == agent.id).scalar() or 0
            resolved_tickets = db.query(func.count(Ticket.id)).filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status == TicketStatus.RESOLVED
            ).scalar() or 0
            
            performance = {
                "agent_id": agent.id,
                "agent_name": agent.username,
                "assigned_tickets": assigned_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": resolved_tickets / assigned_tickets if assigned_tickets > 0 else 0
            }
            agent_performance.append(performance)
        
        # 分类分布
        category_distribution = []
        categories = db.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()
        for category, count in categories:
            category_distribution.append({
                "category": category or "未分类",
                "count": count
            })
        
        return DashboardStats(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            average_resolution_time=average_resolution_time,
            agent_performance=agent_performance,
            category_distribution=category_distribution
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表盘统计信息时发生错误: {str(e)}")
