import requests

# 测试获取待处理工单API
def test_pending_tickets_api():
    print("=== 测试获取待处理工单API ===")
    
    url = "http://localhost:8000/api/v1/agent/tickets/pending"
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"工单数量: {len(data)}")
        else:
            print("API调用失败")
            
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_pending_tickets_api()
    print("\n=== 测试完成 ===")
