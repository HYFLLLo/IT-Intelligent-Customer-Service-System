"""RAG服务模块"""
from typing import Dict, Any, List
from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.retriever import Retriever
from app.services.rag.llm_client import LLMClient


class RAGService:
    """RAG服务类"""
    
    def __init__(self):
        """初始化RAG服务"""
        # 初始化文档处理器
        self.document_processor = DocumentProcessor()
        
        # 初始化检索器
        self.retriever = Retriever()
        
        # 初始化LLM客户端
        self.llm_client = LLMClient()
    
    def add_document(self, document_id: int, title: str, content: str, category: str = None):
        """添加文档到知识库
        
        Args:
            document_id: 文档ID
            title: 文档标题
            content: 文档内容
            category: 文档分类
        """
        self.document_processor.add_document(document_id, title, content, category)
    
    def remove_document(self, document_id: int):
        """从知识库中移除文档
        
        Args:
            document_id: 文档ID
        """
        self.document_processor.remove_document(document_id)
    
    def update_document(self, document_id: int, title: str, content: str, category: str = None):
        """更新知识库中的文档
        
        Args:
            document_id: 文档ID
            title: 文档标题
            content: 文档内容
            category: 文档分类
        """
        self.document_processor.update_document(document_id, title, content, category)
    
    def ask_question(self, query: str, top_k: int = 3, category: str = None, concise: bool = False) -> Dict[str, Any]:
        """处理用户问题
        
        Args:
            query: 用户问题
            top_k: 返回前k个检索结果
            category: 按分类筛选
            concise: 是否生成简洁版回答（员工端使用）
            
        Returns:
            包含回答和置信度的字典
        """
        # 1. 检索相关知识片段
        retrieved_docs = self.retriever.hybrid_retrieve(query, top_k=top_k, category=category)
        
        # 2. 生成回答（员工端使用简洁版）
        llm_result = self.llm_client.generate_answer(query, retrieved_docs, concise=concise)
        
        # 3. 构建最终结果
        result = {
            "answer": llm_result["answer"],
            "confidence": llm_result["confidence"],
            "retrieved_docs": retrieved_docs,
            "usage": llm_result.get("usage", {})
        }
        
        # 4. 添加转人工建议
        if result["confidence"] < 0.7:
            result["suggestion"] = "AI回答的置信度较低，建议提交工单获取进一步帮助。"
        
        return result
    
    def get_document_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息
        
        Returns:
            知识库统计信息
        """
        # 获取集合信息
        collection = self.document_processor.collection
        
        # 获取所有文档
        all_docs = collection.get()
        
        # 统计文档数量
        doc_ids = set()
        for metadata in all_docs.get("metadatas", []):
            if metadata and "document_id" in metadata:
                doc_ids.add(metadata["document_id"])
        
        # 构建统计信息
        stats = {
            "total_segments": len(all_docs.get("ids", [])),
            "total_documents": len(doc_ids),
            "collection_name": collection.name
        }
        
        return stats
