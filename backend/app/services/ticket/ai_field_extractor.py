from typing import Dict, Any
from .field_extractor import FieldExtractor
from ..rag.llm_client import LLMClient
from ...models.ticket import TicketPriority

class AIFieldExtractor(FieldExtractor):
    def __init__(self):
        super().__init__()
        self.llm_client = LLMClient()
    
    def extract_fields(self, content: str) -> Dict[str, Any]:
        
        base_fields = super().extract_fields(content)
        
        ai_enhanced_fields = self._ai_enhance_extraction(content)
        
        
        enhanced_fields = {
            **base_fields,
            **ai_enhanced_fields
        }
        
        return enhanced_fields
    
    def _ai_enhance_extraction(self, content: str) -> Dict[str, Any]:
        """使用AI增强字段提取
        
        Args:
            content: 工单内容
            
        Returns:
            AI增强提取的字段
        """
        try:
            prompt = self._build_extraction_prompt(content)
            
            response = self.llm_client.generate_answer(
                prompt,
                retrieved_docs=[]
            )
            
            extracted_info = self._parse_ai_response(response.get('answer', ''))
            
            return extracted_info
        except Exception as e:
            
            return {}
    
    def _build_extraction_prompt(self, content: str) -> str:
        """构建字段提取的提示模板
        
        Args:
            content: 工单内容
            
        Returns:
            构建好的提示
        """
        return f"""你是一个专业的工单字段提取助手，需要从以下工单内容中提取关键信息：

【工单内容】
{content}

请从上述内容中提取以下字段：
1. priority: 优先级（low、medium、high、urgent）
2. category: 类别（technical、billing、account、support）
3. issue_type: 具体问题类型
4. severity: 严重程度
5. required_skills: 解决该问题所需的技能
6. estimated_effort: 估计解决时间（小时）
7. contact_info: 联系信息（电话、邮箱等）
8. device_info: 设备信息
9. software_version: 软件版本
10. error_messages: 错误信息

请以JSON格式返回提取结果，确保格式正确且字段值合理。"""
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI的响应
        
        Args:
            response: AI的响应内容
            
        Returns:
            解析后的字段
        """
        import json
        
        try:
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                
                if isinstance(parsed, dict):
                    return self._normalize_extracted_fields(parsed)
        except Exception as e:
            pass
        
        return {}
    
    def _normalize_extracted_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """标准化提取的字段
        
        Args:
            fields: 提取的字段
            
        Returns:
            标准化后的字段
        """
        normalized = {}
        
        
        if 'priority' in fields:
            priority_map = {
                'low': TicketPriority.LOW,
                'medium': TicketPriority.MEDIUM,
                'high': TicketPriority.HIGH,
                'urgent': TicketPriority.URGENT
            }
            priority = fields['priority']
            # 检查priority是否已经是TicketPriority枚举对象
            if isinstance(priority, TicketPriority):
                normalized['priority'] = priority
            else:
                # 如果是字符串，转换为小写
                priority_str = priority.lower()
                if priority_str in priority_map:
                    normalized['priority'] = priority_map[priority_str]
        
        
        if 'category' in fields:
            category = fields['category'].lower()
            valid_categories = ['technical', 'billing', 'account', 'support']
            if category in valid_categories:
                normalized['category'] = category
        
        
        if 'issue_type' in fields:
            normalized['issue_type'] = fields['issue_type']
        
        if 'severity' in fields:
            normalized['severity'] = fields['severity']
        
        if 'required_skills' in fields:
            normalized['required_skills'] = fields['required_skills']
        
        if 'estimated_effort' in fields:
            normalized['estimated_effort'] = fields['estimated_effort']
        
        if 'contact_info' in fields:
            normalized['contact_info'] = fields['contact_info']
        
        if 'device_info' in fields:
            normalized['device_info'] = fields['device_info']
        
        if 'software_version' in fields:
            normalized['software_version'] = fields['software_version']
        
        if 'error_messages' in fields:
            normalized['error_messages'] = fields['error_messages']
        
        return normalized
    
    def extract_complex_fields(self, content: str) -> Dict[str, Any]:
        """提取复杂字段
        
        Args:
            content: 工单内容
            
        Returns:
            提取的复杂字段
        """
        return self._ai_enhance_extraction(content)