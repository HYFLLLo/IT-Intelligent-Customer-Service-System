"""测试RAG服务的知识库检索功能"""
import sys
import os

# 添加backend目录到Python路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.services.rag import RAGService
from app.services.rag.retriever import Retriever


def test_retriever():
    """测试检索器"""
    print("=== 测试检索器 ===")
    retriever = Retriever()
    
    # 测试查询
    test_queries = [
        "数据同步中断",
        "如何重置密码",
        "打印机连接问题",
        "Office安装失败"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        results = retriever.hybrid_retrieve(query, top_k=3)
        print(f"检索到 {len(results)} 个结果")
        for i, result in enumerate(results):
            print(f"\n结果 {i+1}:")
            print(f"内容: {result['content'][:200]}...")
            print(f"关键词分数: {result.get('keyword_score', 0)}")
            print(f"综合得分: {result.get('comprehensive_score', 0)}")
            print(f"距离: {result.get('distance', 'N/A')}")


def test_rag_service():
    """测试RAG服务"""
    print("\n=== 测试RAG服务 ===")
    rag_service = RAGService()
    
    # 测试问题
    test_questions = [
        "数据同步中断，我的解决方法有哪些",
        "如何重置密码？",
        "打印机连接不上怎么办？",
        "Office安装失败了，怎么处理？"
    ]
    
    for question in test_questions:
        print(f"\n问题: {question}")
        result = rag_service.ask_question(question)
        print(f"回答: {result['answer']}")
        print(f"置信度: {result['confidence']}")
        print(f"检索到的文档数: {len(result['retrieved_docs'])}")
        if result['retrieved_docs']:
            print("\n检索到的文档:")
            for i, doc in enumerate(result['retrieved_docs']):
                print(f"文档 {i+1}: {doc['content'][:100]}...")


if __name__ == "__main__":
    try:
        test_retriever()
        test_rag_service()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
