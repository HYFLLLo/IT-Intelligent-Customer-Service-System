from typing import Dict, Any
from ...models.ticket import TicketPriority

class FieldExtractor:
    def __init__(self):
        self.priority_keywords = {
            'urgent': ['紧急', 'urgent', 'emergency', '立刻', '马上', '紧急情况'],
            'high': ['高', 'high', '重要', 'serious', 'critical'],
            'medium': ['中', 'medium', '一般', 'normal', 'regular'],
            'low': ['低', 'low', '轻微', 'minor', 'small']
        }
        
        self.category_keywords = {
            'technical': ['技术', 'technical', '系统', 'system', '软件', 'software', '硬件', 'hardware', '网络', 'network'],
            'billing': ['账单', 'billing', '费用', 'payment', '收费', 'charge', '发票', 'invoice'],
            'account': ['账户', 'account', '登录', 'login', '注册', 'register', '密码', 'password'],
            'support': ['支持', 'support', '帮助', 'help', '咨询', 'inquiry', '问题', 'problem']
        }
    
    def extract_fields(self, content: str) -> Dict[str, Any]:
        fields = {
            'priority': TicketPriority.MEDIUM,
            'category': None
        }
        
        fields['priority'] = self._extract_priority(content)
        fields['category'] = self._extract_category(content)
        
        return fields
    
    def _extract_priority(self, content: str) -> TicketPriority:
        content_lower = content.lower()
        
        for priority_level, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    return getattr(TicketPriority, priority_level.upper(), TicketPriority.MEDIUM)
        
        return TicketPriority.MEDIUM
    
    def _extract_category(self, content: str) -> str:
        content_lower = content.lower()
        
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def extract_contact_info(self, content: str) -> Dict[str, str]:
        import re
        contact_info = {}
        
        phone_pattern = r'1[3-9]\d{9}'
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        phone_matches = re.findall(phone_pattern, content)
        email_matches = re.findall(email_pattern, content)
        
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
        if email_matches:
            contact_info['email'] = email_matches[0]
        
        return contact_info
    
    def extract_product_info(self, content: str) -> Dict[str, str]:
        
        product_info = {}
        
        product_keywords = ['产品', 'product', '型号', 'model', '版本', 'version']
        
        content_lower = content.lower()
        for keyword in product_keywords:
            if keyword in content_lower:
                product_info['has_product_info'] = True
                break
        
        return product_info