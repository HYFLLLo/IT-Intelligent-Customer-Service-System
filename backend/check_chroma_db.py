from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.retriever import Retriever

# 初始化文档处理器
processor = DocumentProcessor()
collection = processor.collection

# 获取所有文档
all_docs = collection.get()
print(f"总共有 {len(all_docs.get('ids', []))} 个知识片段")

# 统计文档数量
doc_ids = set()
for meta in all_docs.get('metadatas', []):
    if meta and 'document_id' in meta:
        doc_ids.add(meta['document_id'])
print(f"总共有 {len(doc_ids)} 个文档")

# 打印前3个文档的内容
print("\n前3个文档的内容:")
for i, doc in enumerate(all_docs.get('documents', [])[:3]):
    print(f"文档 {i+1} 内容: {doc[:200]}...")

# 测试检索
print("\n测试检索:")
test_query = "无法登录Google Docs账户；登录后无法打开文档文件"
retriever = Retriever()
retrieved_docs = retriever.hybrid_retrieve(test_query, top_k=3)
print(f"检索到 {len(retrieved_docs)} 篇相关知识库文档")

# 打印检索结果
for i, doc in enumerate(retrieved_docs):
    print(f"检索结果 {i+1} 内容:")
    print(doc['content'])
    print(f"相似度分数: {doc.get('comprehensive_score', 'N/A')}")
    print("-" * 80)
