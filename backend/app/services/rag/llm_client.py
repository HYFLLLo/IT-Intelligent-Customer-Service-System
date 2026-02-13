"""LLM客户端模块"""
import requests
import json
from typing import Dict, Any
from app.config.settings import settings


class LLMClient:
    """LLM客户端类"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def build_prompt(self, query: str, retrieved_docs: list, concise: bool = False) -> str:
        """构建Prompt模板
        
        Args:
            query: 用户问题
            retrieved_docs: 检索到的知识片段
            concise: 是否生成简洁版回答（员工端使用）
            
        Returns:
            构建好的Prompt
        """
        if concise:
            # 员工端简洁版 Prompt
            system_prompt = '''你是企业IT自助服务助手。基于知识库内容，为员工提供简洁、准确、可立即操作的解决方案。

【核心要求】
1. 简洁：直接给出答案，不要冗长解释
2. 准确：严格基于知识库内容
3. 可操作：提供具体步骤，员工能立即执行
4. 结构化：分点列出，便于快速阅读
5. 格式要求：不要使用Markdown格式（如#、*、-等），使用纯文本和序号

【回答格式】
先给出1-2句话的核心解决方案
然后列出3-5个具体操作步骤（用1. 2. 3.格式）
最后如有必要，给出1条关键注意事项'''
            max_words = "200-300字"
            knowledge_limit = 500
        else:
            # 坐席端详细版 Prompt
            system_prompt = '''你是企业级IT智能客服系统的技术支持专家。基于知识库内容，为员工提供专业、准确的IT问题解决方案。

【核心要求】
1. 准确性：严格基于知识库内容，不添加未经验证的信息
2. 实用性：提供可操作的详细步骤
3. 结构化：使用清晰的层次结构
4. 安全性：强调操作风险和注意事项
5. 格式要求：不要使用Markdown格式（如#、##、*、-、>等符号），使用纯文本和序号

【回答结构】
【问题诊断】分析可能原因（用1. 2. 3.格式）
【解决方案】详细操作步骤（用步骤1：步骤2：格式）
【注意事项】风险提示
【预防建议】避免再次发生
【总结】核心解决思路'''
            max_words = "600-800字"
            knowledge_limit = 800
        
        # 构建知识片段部分
        knowledge_parts = []
        for i, doc in enumerate(retrieved_docs):
            source_info = doc.get('source', '知识库')
            content = doc.get('content', '')[:knowledge_limit]
            knowledge_part = f"[来源{i+1}: {source_info}]\n{content}\n"
            knowledge_parts.append(knowledge_part)
        knowledge_text = "\n".join(knowledge_parts)
        
        # 构建完整Prompt
        prompt = f"{system_prompt}\n\n【知识库参考】\n{knowledge_text}\n\n【用户问题】\n{query}\n\n请基于以上知识库内容，提供专业的解决方案。回答控制在{max_words}。"
        
        return prompt
    
    def generate_answer(self, query: str, retrieved_docs: list, concise: bool = False) -> Dict[str, Any]:
        """生成回答
        
        Args:
            query: 用户问题
            retrieved_docs: 检索到的知识片段
            concise: 是否生成简洁版回答（员工端使用）
            
        Returns:
            包含回答和置信度的字典
        """
        # 构建Prompt
        prompt = self.build_prompt(query, retrieved_docs, concise)
        
        # 构建请求体
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5 if concise else 0.7,
            "max_tokens": 400 if concise else 1200,
            "top_p": 0.95,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        try:
            # 调用DeepSeek API
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            # 处理响应
            response.raise_for_status()
            result = response.json()
            
            # 提取回答
            answer = result["choices"][0]["message"]["content"]
            
            # 计算置信度
            confidence = self._calculate_confidence(retrieved_docs, answer)
            
            return {
                "answer": answer,
                "confidence": confidence,
                "usage": result.get("usage", {})
            }
        
        except Exception as e:
            # 异常处理
            return {
                "answer": "抱歉，AI服务暂时不可用，请稍后再试或提交工单获取帮助。",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _calculate_confidence(self, retrieved_docs: list, answer: str) -> float:
        """计算回答的置信度
        
        Args:
            retrieved_docs: 检索到的知识片段
            answer: 生成的回答
            
        Returns:
            置信度（0-1之间）
        """
        # 简化实现：基于检索结果的数量和质量计算置信度
        if not retrieved_docs:
            return 0.3
        
        # 基础置信度
        base_confidence = 0.7
        
        # 基于检索结果数量调整
        doc_count = len(retrieved_docs)
        if doc_count >= 3:
            base_confidence += 0.2
        elif doc_count == 2:
            base_confidence += 0.1
        
        # 基于回答长度和内容调整
        if len(answer) > 100:
            base_confidence += 0.05
        
        # 确保置信度在0-1之间
        return min(base_confidence, 1.0)
    
    def extract_fields(self, query: str, retrieved_docs: list) -> list:
        """从查询和知识片段中提取关键字段
        
        Args:
            query: 用户问题
            retrieved_docs: 检索到的知识片段
            
        Returns:
            提取的字段列表，每个字段包含name和value
        """
        # 构建字段提取的prompt
        knowledge_text = "\n".join([doc.get('content', '')[:500] for doc in retrieved_docs])
        
        prompt = f'''请从以下工单内容和知识库信息中提取3个最关键的信息字段。

【工单内容】
{query}

【知识库参考】
{knowledge_text}

请提取以下类型的字段（根据内容选择最相关的3个）：
- 设备型号/设备类型（如：MacBook Pro、ThinkPad X1、打印机等）
- 问题类型/故障类别（如：网络连接、系统崩溃、软件安装等）
- 操作系统（如：Windows 11、macOS、Linux等）
- 软件名称（如：Office 365、Chrome、企业邮箱等）
- 网络环境（如：公司WiFi、有线网络、VPN等）
- 账户类型（如：域账户、本地账户、企业邮箱等）

请以JSON格式返回，格式如下：
[
  {{"name": "字段名称", "value": "提取的值"}},
  {{"name": "字段名称", "value": "提取的值"}},
  {{"name": "字段名称", "value": "提取的值"}}
]

如果无法确定某个字段的值，请使用"未知"或"未明确提及"。只返回JSON数组，不要其他说明。'''
        
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # 解析JSON响应
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\[.*\]', answer, re.DOTALL)
            if json_match:
                fields_data = json.loads(json_match.group())
                # 确保格式正确
                return [{"name": f.get("name", ""), "value": f.get("value", "")} for f in fields_data[:3]]
            return []
        except Exception as e:
            print(f"字段提取失败: {e}")
            # 返回基于关键词的简单提取结果
            return self._simple_field_extraction(query, retrieved_docs)
    
    def _simple_field_extraction(self, query: str, retrieved_docs: list) -> list:
        """简单的基于规则的字段提取（备用方案）"""
        fields = []
        text = query.lower()
        knowledge_text = " ".join([doc.get('content', '').lower() for doc in retrieved_docs])
        combined_text = text + " " + knowledge_text
        
        # 提取设备型号
        devices = {
            'macbook': 'MacBook',
            'thinkpad': 'ThinkPad',
            'dell': 'Dell',
            'hp': 'HP',
            'lenovo': 'Lenovo',
            'iphone': 'iPhone',
            'ipad': 'iPad',
            'android': 'Android设备',
            '打印机': '打印机',
            '路由器': '路由器'
        }
        for key, value in devices.items():
            if key in combined_text:
                fields.append({"name": "设备类型", "value": value})
                break
        
        # 提取问题类型
        problem_types = {
            '网络': '网络连接',
            'wifi': 'WiFi连接',
            '登录': '账户登录',
            '密码': '密码问题',
            '无法开机': '硬件故障',
            '蓝屏': '系统崩溃',
            '死机': '系统无响应',
            '打印': '打印问题',
            '软件': '软件问题',
            '邮箱': '邮箱问题'
        }
        for key, value in problem_types.items():
            if key in combined_text:
                fields.append({"name": "问题类型", "value": value})
                break
        
        # 提取操作系统
        os_types = {
            'windows 11': 'Windows 11',
            'windows 10': 'Windows 10',
            'windows': 'Windows',
            'macos': 'macOS',
            'mac': 'macOS',
            'linux': 'Linux',
            'ios': 'iOS',
            'android': 'Android'
        }
        for key, value in os_types.items():
            if key in combined_text:
                fields.append({"name": "操作系统", "value": value})
                break
        
        # 如果提取不到3个，补充默认值
        default_fields = [
            {"name": "设备类型", "value": "未明确提及"},
            {"name": "问题类型", "value": "待进一步确认"},
            {"name": "操作系统", "value": "未明确提及"}
        ]
        
        while len(fields) < 3:
            for default in default_fields:
                if not any(f["name"] == default["name"] for f in fields):
                    fields.append(default)
                    break
            if len(fields) < 3:
                idx = len(fields) + 1
                fields.append({"name": "其他信息" + str(idx), "value": "未明确提及"})

        return fields[:3]
