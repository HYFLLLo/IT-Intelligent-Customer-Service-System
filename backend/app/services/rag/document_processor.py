"""文档处理模块"""
import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb import PersistentClient
from app.config.settings import settings


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        """初始化文档处理器"""
        # 初始化Chroma客户端
        self.chroma_client = PersistentClient(
            path=settings.CHROMA_DB_PATH
        )
        
        # 获取或创建知识库集合
        self.collection = self.chroma_client.get_or_create_collection(
            name="it_knowledge_base"
        )
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def split_document(self, content: str, document_id: str) -> List[Dict[str, Any]]:
        """分割文档为多个片段
        
        Args:
            content: 文档内容
            document_id: 文档ID
            
        Returns:
            文档片段列表
        """
        # 分割文本
        chunks = self.text_splitter.split_text(content)
        
        # 构建片段元素
        segments = []
        for i, chunk in enumerate(chunks):
            segment = {
                "id": f"{document_id}_{i}",
                "content": chunk,
                "document_id": document_id,
                "segment_index": i
            }
            segments.append(segment)
        
        return segments
    
    def add_document(self, document_id: str, content: str, metadata: dict):
        """添加文档到知识库
        
        Args:
            document_id: 文档ID
            content: 文档内容
            metadata: 文档元数据
        """
        # 分割文档
        segments = self.split_document(content, document_id)
        
        # 获取片段ID、内容和元数据
        ids = [segment["id"] for segment in segments]
        documents = [segment["content"] for segment in segments]
        metadatas = [
            {
                "document_id": segment["document_id"],
                "segment_index": segment["segment_index"],
                "title": metadata.get("title"),
                "category": metadata.get("category"),
                "tags": ",".join(metadata.get("tags", [])) if isinstance(metadata.get("tags"), list) else metadata.get("tags")
            }
            for segment in segments
        ]
        
        # 添加到Chroma向量数据库
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def remove_document(self, document_id: str):
        """从知识库中删除文档
        
        Args:
            document_id: 文档ID
        """
        # 获取文档的所有片段
        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        # 删除片段
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
    
    def update_document(self, document_id: str, content: str, metadata: dict):
        """更新知识库中的文档
        
        Args:
            document_id: 文档ID
            content: 文档内容
            metadata: 文档元数据
        """
        # 先删除旧文档
        self.remove_document(document_id)
        # 添加新文档
        self.add_document(document_id, content, metadata)

