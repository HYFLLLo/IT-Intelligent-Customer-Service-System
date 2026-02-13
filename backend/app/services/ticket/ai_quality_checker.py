from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from ..rag.llm_client import LLMClient
from ...models.quality import QualityCheck, QualityRule
from ...models.ticket import Ticket, TicketResponse

class AIQualityChecker:
    def __init__(self, db: Session):
        self.db = db
        self.llm_client = LLMClient()
        self.quality_rules = self._load_quality_rules()
    
    def check_ticket_quality(self, ticket_id: int) -> Dict[str, Any]:
        """检查工单质量
        
        Args:
            ticket_id: 工单ID
            
        Returns:
            质检结果
        """
        ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return {"error": "工单不存在"}
        
        responses = self.db.query(TicketResponse).filter(
            TicketResponse.ticket_id == ticket_id
        ).all()
        
        quality_check = self._perform_quality_check(ticket, responses)
        
        self._save_quality_check(ticket_id, quality_check)
        
        return quality_check
    
    def _perform_quality_check(self, ticket: Ticket, responses: List[TicketResponse]) -> Dict[str, Any]:
        """执行质量检查
        
        Args:
            ticket: 工单对象
            responses: 工单回复列表
            
        Returns:
            质检结果
        """
        base_score = self._calculate_base_score(ticket, responses)
        
        ai_enhanced_result = self._ai_enhance_quality_check(ticket, responses)
        
        final_score = self._calculate_final_score(base_score, ai_enhanced_result)
        
        return {
            "score": final_score,
            "base_score": base_score,
            "ai_score": ai_enhanced_result.get('score', base_score),
            "comments": ai_enhanced_result.get('comments', []),
            "suggestions": ai_enhanced_result.get('suggestions', []),
            "detailed_analysis": ai_enhanced_result.get('detailed_analysis', {})
        }
    
    def _calculate_base_score(self, ticket: Ticket, responses: List[TicketResponse]) -> float:
        """计算基础分数
        
        Args:
            ticket: 工单对象
            responses: 工单回复列表
            
        Returns:
            基础分数
        """
        score = 100.0
        
        if not responses:
            score -= 30
        
        response_time_score = self._calculate_response_time_score(ticket, responses)
        score += response_time_score
        
        resolution_score = self._calculate_resolution_score(ticket)
        score += resolution_score
        
        return max(0, min(100, score))
    
    def _calculate_response_time_score(self, ticket: Ticket, responses: List[TicketResponse]) -> float:
        """计算响应时间分数
        
        Args:
            ticket: 工单对象
            responses: 工单回复列表
            
        Returns:
            响应时间分数
        """
        if not responses:
            return -20
        
        return 0
    
    def _calculate_resolution_score(self, ticket: Ticket) -> float:
        """计算解决情况分数
        
        Args:
            ticket: 工单对象
            
        Returns:
            解决情况分数
        """
        if ticket.status in ['resolved', 'closed']:
            return 10
        return -10
    
    def _ai_enhance_quality_check(self, ticket: Ticket, responses: List[TicketResponse]) -> Dict[str, Any]:
        """使用AI增强质量检查
        
        Args:
            ticket: 工单对象
            responses: 工单回复列表
            
        Returns:
            AI增强的质检结果
        """
        try:
            prompt = self._build_quality_check_prompt(ticket, responses)
            
            response = self.llm_client.generate_answer(
                prompt,
                retrieved_docs=[]
            )
            
            analysis = self._parse_ai_analysis(response.get('answer', ''))
            
            return analysis
        except Exception as e:
            
            return {
                "score": 50,
                "comments": ["AI质检失败，使用默认分数"],
                "suggestions": [],
                "detailed_analysis": {}
            }
    
    def _build_quality_check_prompt(self, ticket: Ticket, responses: List[TicketResponse]) -> str:
        """构建质量检查的提示模板
        
        Args:
            ticket: 工单对象
            responses: 工单回复列表
            
        Returns:
            构建好的提示
        """
        responses_text = "\n".join([
            f"客服回复 {i+1} (时间: {r.created_at}):\n{r.content}"
            for i, r in enumerate(responses)
        ])
        
        return f"""你是一个专业的工单质量检查员，需要对以下工单及其回复进行质量评估：

【工单信息】
标题：{ticket.title}
内容：{ticket.content}
优先级：{ticket.priority.value}
类别：{ticket.category}
状态：{ticket.status.value}
创建时间：{ticket.created_at}

【客服回复】
{responses_text if responses else "无回复"}

请从以下维度进行评估：
1. 响应及时性
2. 问题理解准确性
3. 解决方案有效性
4. 沟通专业性
5. 客户满意度
6. 问题解决完整性
7. 技术准确性
8. 服务态度

每个维度满分10分，请给出详细的分析和改进建议。

最终评分标准：
- 90-100分：优秀
- 80-89分：良好
- 70-79分：一般
- 60-69分：及格
- 60分以下：不及格

请以JSON格式返回评估结果，包含：
1. score: 最终评分
2. comments: 问题描述
3. suggestions: 改进建议
4. detailed_analysis: 各维度详细分析

确保分析客观、专业，建议具体可行。"""
    
    def _parse_ai_analysis(self, response: str) -> Dict[str, Any]:
        """解析AI的分析结果
        
        Args:
            response: AI的响应内容
            
        Returns:
            解析后的分析结果
        """
        import json
        
        try:
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                if isinstance(parsed, dict):
                    return {
                        "score": float(parsed.get('score', 50)),
                        "comments": parsed.get('comments', []),
                        "suggestions": parsed.get('suggestions', []),
                        "detailed_analysis": parsed.get('detailed_analysis', {})
                    }
        except Exception as e:
            pass
        
        return {
            "score": 50,
            "comments": ["无法解析AI分析结果"],
            "suggestions": [],
            "detailed_analysis": {}
        }
    
    def _calculate_final_score(self, base_score: float, ai_result: Dict[str, Any]) -> float:
        """计算最终分数
        
        Args:
            base_score: 基础分数
            ai_result: AI分析结果
            
        Returns:
            最终分数
        """
        ai_score = ai_result.get('score', base_score)
        
        final_score = (base_score * 0.4) + (ai_score * 0.6)
        
        return max(0, min(100, final_score))
    
    def _save_quality_check(self, ticket_id: int, quality_result: Dict[str, Any]):
        """保存质量检查结果
        
        Args:
            ticket_id: 工单ID
            quality_result: 质检结果
        """
        quality_check = QualityCheck(
            ticket_id=ticket_id,
            check_time=datetime.now().isoformat(),
            score=str(quality_result.get('score', 0)),
            comments=str(quality_result.get('comments', []))
        )
        
        self.db.add(quality_check)
        self.db.commit()
        self.db.refresh(quality_check)
        
        # 创建通知
        self._create_quality_report_notification(ticket_id, quality_result, quality_check.id)
    
    def _load_quality_rules(self) -> List[QualityRule]:
        """加载质量规则
        
        Returns:
            质量规则列表
        """
        return self.db.query(QualityRule).all()
    
    def _create_quality_report_notification(self, ticket_id: int, quality_result: Dict[str, Any], report_id: int):
        """创建质检报告通知
        
        Args:
            ticket_id: 工单ID
            quality_result: 质检结果
            report_id: 质检报告ID
        """
        try:
            # 获取工单信息
            ticket = self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                return
            
            # 获取工单回复（处理结果）
            from app.models.ticket import TicketResponse
            responses = self.db.query(TicketResponse).filter(
                TicketResponse.ticket_id == ticket_id
            ).all()
            
            # 构建处理结果内容
            response_content = "\n".join([
                f"客服回复 {i+1} (时间: {r.created_at}):\n{r.content}"
                for i, r in enumerate(responses)
            ]) if responses else "暂无处理结果"
            
            # 计算评分（转换为5分制）
            score = float(quality_result.get('score', 0)) / 20
            score = round(score, 1)
            
            # 构建通知标题和内容
            title = f"质检报告：{ticket.title}"
            content = f"您的工单处理已完成质检，评分：{score}\n\n工单内容：{ticket.content}\n\n处理结果：{response_content}"
            
            # 构建完整的质检报告数据（用于员工侧显示）
            import json
            
            # 获取用户和部门信息
            from app.models.user import User
            user = self.db.query(User).filter(User.id == ticket.user_id).first()
            username = user.username if user else "未知用户"
            department = user.department if user else "未知部门"
            
            # 构建详细的评分项（与坐席侧一致）
            score_details = []
            detailed_analysis = quality_result.get('detailed_analysis', {})
            
            # 基础评分项
            if 'response_time' in detailed_analysis:
                score_details.append({
                    'name': '响应速度',
                    'score': detailed_analysis.get('response_time', {}).get('score', 20),
                    'maxScore': 20,
                    'description': detailed_analysis.get('response_time', {}).get('comment', '响应及时')
                })
            
            if 'solution_quality' in detailed_analysis:
                score_details.append({
                    'name': '解决方案',
                    'score': detailed_analysis.get('solution_quality', {}).get('score', 25),
                    'maxScore': 25,
                    'description': detailed_analysis.get('solution_quality', {}).get('comment', '方案合理')
                })
            
            if 'communication' in detailed_analysis:
                score_details.append({
                    'name': '沟通态度',
                    'score': detailed_analysis.get('communication', {}).get('score', 20),
                    'maxScore': 20,
                    'description': detailed_analysis.get('communication', {}).get('comment', '态度友好')
                })
            
            if 'professionalism' in detailed_analysis:
                score_details.append({
                    'name': '专业性',
                    'score': detailed_analysis.get('professionalism', {}).get('score', 20),
                    'maxScore': 20,
                    'description': detailed_analysis.get('professionalism', {}).get('comment', '专业准确')
                })
            
            if 'follow_up' in detailed_analysis:
                score_details.append({
                    'name': '跟进处理',
                    'score': detailed_analysis.get('follow_up', {}).get('score', 15),
                    'maxScore': 15,
                    'description': detailed_analysis.get('follow_up', {}).get('comment', '跟进及时')
                })
            
            # 如果没有详细的分析数据，使用默认的评分项
            if not score_details:
                score_details = [
                    {'name': '响应速度', 'score': 18, 'maxScore': 20, 'description': '响应及时'},
                    {'name': '解决方案', 'score': 22, 'maxScore': 25, 'description': '方案合理'},
                    {'name': '沟通态度', 'score': 19, 'maxScore': 20, 'description': '态度友好'},
                    {'name': '专业性', 'score': 18, 'maxScore': 20, 'description': '专业准确'},
                    {'name': '跟进处理', 'score': 14, 'maxScore': 15, 'description': '跟进及时'}
                ]
            
            # 构建完整的报告数据
            full_report_data = {
                'id': report_id,
                'ticketId': ticket_id,
                'title': ticket.title,
                'content': ticket.content,
                'response': response_content,
                'score': score,
                'user': username,
                'department': department,
                'createdAt': datetime.now().isoformat(),
                'scoreDetails': score_details,
                'comments': quality_result.get('comments', []),
                'suggestions': quality_result.get('suggestions', []),
                'detailedAnalysis': detailed_analysis,
                'baseScore': quality_result.get('base_score', 0),
                'aiScore': quality_result.get('ai_score', 0)
            }
            
            # 创建通知
            from app.models.user import Notification
            notification = Notification(
                user_id=ticket.user_id,
                type="quality_report",
                title=title,
                content=content,  # 使用包含处理结果的内容
                response=response_content,  # 设置工程师回复的内容
                is_read=False,
                created_at=datetime.now().isoformat(),
                report_id=report_id,
                ticket_id=ticket_id,
                score=int(score * 10),  # 存储为整数，例如4.5存储为45
                report_data=json.dumps(full_report_data, ensure_ascii=False)  # 存储完整的报告数据
            )
            
            self.db.add(notification)
            self.db.commit()
            print(f"✅ 创建质检报告通知成功，包含完整报告数据，report_id: {report_id}")
        except Exception as e:
            print(f"创建质检报告通知失败：{str(e)}")
            import traceback
            traceback.print_exc()
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """获取质量统计信息
        
        Returns:
            质量统计信息
        """
        all_checks = self.db.query(QualityCheck).all()
        
        if not all_checks:
            return {
                "total_checks": 0,
                "average_score": 0,
                "score_distribution": {}
            }
        
        scores = [float(check.score) for check in all_checks if check.score]
        average_score = sum(scores) / len(scores) if scores else 0
        
        score_distribution = {
            "excellent": len([s for s in scores if s >= 90]),
            "good": len([s for s in scores if 80 <= s < 90]),
            "average": len([s for s in scores if 70 <= s < 80]),
            "pass": len([s for s in scores if 60 <= s < 70]),
            "fail": len([s for s in scores if s < 60])
        }
        
        return {
            "total_checks": len(all_checks),
            "average_score": average_score,
            "score_distribution": score_distribution
        }