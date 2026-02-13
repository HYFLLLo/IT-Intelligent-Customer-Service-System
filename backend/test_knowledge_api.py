import requests
import json

# 测试知识库API
def test_knowledge_api():
    print("=== 测试知识库API ===")
    
    # 测试获取知识库列表
    url = "http://localhost:8000/api/v1/admin/knowledge"
    
    try:
        response = requests.get(url)
        print(f"响应状态码: {response.status_code}")
        
        # 打印原始响应内容
        print(f"原始响应内容: {response.text}")
        
        # 尝试解析JSON
        if response.status_code == 200:
            data = response.json()
            print(f"知识库文章数量: {len(data)}")
            
            # 打印每篇文章的标题和内容预览
            for i, article in enumerate(data):
                print(f"\n文章 {i+1}:")
                print(f"标题: {article.get('title')}")
                print(f"内容预览: {article.get('content', '')[:100]}...")
                print(f"分类: {article.get('category')}")
                print(f"更新时间: {article.get('updated_at')}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_knowledge_api()
