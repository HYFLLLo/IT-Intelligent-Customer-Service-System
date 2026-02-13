"""检索器模块"""
from typing import List, Dict, Any
from chromadb import PersistentClient
from app.config.settings import settings


class Retriever:
    """检索器"""
    
    def __init__(self):
        """初始化检索器"""
        # 初始化Chroma客户端
        self.chroma_client = PersistentClient(
            path=settings.CHROMA_DB_PATH
        )
        
        # 获取知识库集合
        self.collection = self.chroma_client.get_collection(
            name="it_knowledge_base"
        )
    
    def retrieve(self, query: str, top_k: int = 3, category: str = None) -> List[Dict[str, Any]]:
        """�������֪ʶƬ��
        
        Args:
            query: �û���ѯ
            top_k: ����ǰk�����
            category: ������ɸѡ
            
        Returns:
            ���֪ʶƬ���б�
        """
        # ������ѯ����
        query_kwargs = {
            "query_texts": [query],
            "n_results": top_k
        }
        if category:
            query_kwargs["where"] = {"category": category}
        
        # ִ����������
        results = self.collection.query(**query_kwargs)
        
        # �����������
        retrieved_docs = []
        for i in range(len(results["ids"][0])):
            doc = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None
            }
            retrieved_docs.append(doc)
        
        return retrieved_docs
    
    def hybrid_retrieve(self, query: str, top_k: int = 3, category: str = None) -> List[Dict[str, Any]]:
        """混合检索（向量检索+关键词匹配）
        
        Args:
            query: 用户查询
            top_k: 返回前k个结果
            category: 分类筛选
            
        Returns:
            相关知识片段列表
        """
        # 构建所有文档列表
        all_documents = []
        
        # 获取所有文档
        try:
            # 直接使用 ChromaDB 的 API 获取所有文档
            from app.config.settings import settings
            import chromadb
            
            # 初始化 Chroma 客户端
            chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            
            # 获取知识库集合
            collection = chroma_client.get_collection(name="it_knowledge_base")
            
            # 获取所有文档
            all_docs = collection.get()
            
            # 处理返回结果
            ids = all_docs.get("ids", [])
            documents = all_docs.get("documents", [])
            metadatas = all_docs.get("metadatas", [])
            
            # 构建文档列表
            for i in range(len(ids)):
                doc = {
                    "id": ids[i],
                    "content": documents[i],
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": 0
                }
                all_documents.append(doc)
            
            print(f"总共获取到 {len(all_documents)} 个文档")
            print(f"查询文本: {query}")
            
            # 计算每个文档的关键词匹配分数
            scored_docs = []
            for doc in all_documents:
                # 跳过重复的文档
                if doc["id"] in [d["id"] for d in scored_docs]:
                    continue
                
                # 计算关键词匹配分数
                score = self._calculate_keyword_score(query, doc["content"])
                doc["keyword_score"] = score
                scored_docs.append(doc)
            
            # 按关键词匹配分数排序
            scored_docs.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)
            
            # 获取向量检索结果
            vector_results = self.retrieve(query, top_k=top_k * 2, category=category)
            
            # 为向量检索结果计算关键词匹配分数
            for doc in vector_results:
                if doc["id"] not in [d["id"] for d in scored_docs]:
                    score = self._calculate_keyword_score(query, doc["content"])
                    doc["keyword_score"] = score
                    scored_docs.append(doc)
            
            # 结合向量检索和关键词匹配的结果
            # 为每个文档计算综合分数
            for doc in scored_docs:
                # 向量检索的相似度分数（距离越小越好）
                vector_score = 1.0 - (doc.get("distance", 1.0) / 2.0) if doc.get("distance") else 0.0
                # 关键词匹配分数（归一化）
                keyword_score = min(doc.get("keyword_score", 0) / 500.0, 1.0)
                # 综合分数（向量检索占40%，关键词匹配占60%）
                comprehensive_score = vector_score * 0.4 + keyword_score * 0.6
                doc["comprehensive_score"] = comprehensive_score
            
            # 按综合分数排序
            scored_docs.sort(key=lambda x: x.get("comprehensive_score", 0), reverse=True)
            
            # 提取前top_k个结果
            final_results = scored_docs[:top_k]
            
            # 打印检索结果
            print("\n检索结果:")
            for i, doc in enumerate(final_results):
                print(f"结果 {i+1} - 综合分数: {doc.get('comprehensive_score', 0):.4f}, 关键词分数: {doc.get('keyword_score', 0)}")
                print(f"内容: {doc['content'][:200]}...")
                print("-" * 80)
            
        except Exception as e:
            print(f"检索时发生错误: {e}")
            # 如果发生错误，使用向量检索的结果
            vector_results = self.retrieve(query, top_k=top_k, category=category)
            final_results = vector_results
        
        return final_results
    
    def _calculate_keyword_score(self, query: str, content: str) -> int:
        """计算关键词匹配分数
        
        Args:
            query: 查询文本
            content: 文档内容
            
        Returns:
            匹配度分数
        """
        # 对查询和内容进行处理
        query_text = query
        content_text = content
        score = 0
        
        # 检查完整查询是否在内容中
        if query_text in content_text:
            score += 100  # 大幅增加完整匹配的分数
        
        # 提取查询中的核心关键词
        # 首先，检查常见的技术术语和问题类型
        common_terms = [
            "数据同步", "同步中断", "同步失败", "文件上传", "文件下载",
            "重置密码", "密码重置", "打印机连接", "连接问题",
            "Office安装", "安装失败", "网络连接", "无法连接",
            "Google Docs", "google docs", "登录", "无法登录", "登录失败",
            "无法开机", "无法启动", "开机失败", "启动失败", "电源按钮",
            "黑屏", "蓝屏", "死机", "重启", "崩溃",
            "硬件故障", "软件故障", "系统错误", "驱动问题", "病毒感染"
        ]
        
        for term in common_terms:
            if term in query_text and term in content_text:
                score += 50  # 增加重要术语的分数
        
        # 检查查询中的每个词是否在内容中（针对中文分词）
        # 简单处理：检查查询中的每个字符序列
        # 对于中文，我们可以检查2-4个字符的组合
        for i in range(len(query_text)):
            for j in range(i+2, min(i+5, len(query_text)+1)):
                keyword = query_text[i:j]
                if keyword in content_text:
                    score += 10  # 增加中文关键词的分数
        
        # 对于英文单词，使用传统的分词方法
        for word in query_text.split():
            if len(word) > 2 and word in content_text:
                score += 20  # 增加英文关键词的分数
        
        # 检查内容中是否包含问题解决方案的关键词
        solution_terms = ["解决步骤", "解决方案", "如何处理", "怎么办", "步骤", "方法"]
        for term in solution_terms:
            if term in content_text:
                score += 5
        
        # 特别处理Google Docs相关问题
        if "Google Docs" in query_text or "google docs" in query_text:
            if "Google Docs" in content_text or "google docs" in content_text:
                score += 200  # 大幅增加Google Docs相关内容的分数
        
        # 特别处理登录相关问题
        if "登录" in query_text:
            if "登录" in content_text:
                score += 150  # 大幅增加登录相关内容的分数
        
        # 特别处理无法打开文档问题
        if "无法打开文档" in query_text or "无法打开文件" in query_text:
            if "无法打开文档" in content_text or "无法打开文件" in content_text:
                score += 100  # 大幅增加无法打开文档相关内容的分数
        
        # 特别处理计算机无法开机问题
        if any(term in query_text for term in ["无法开机", "无法启动", "开机失败", "启动失败", "电源按钮"]):
            if any(term in content_text for term in ["无法开机", "无法启动", "开机失败", "启动失败", "电源按钮"]):
                score += 200  # 大幅增加计算机无法开机相关内容的分数
        
        # 特别处理硬件故障问题
        if "硬件" in query_text:
            if "硬件" in content_text:
                score += 150  # 大幅增加硬件故障相关内容的分数
        
        # 特别处理软件故障问题
        if "软件" in query_text:
            if "软件" in content_text:
                score += 150  # 大幅增加软件故障相关内容的分数
        
        return score

