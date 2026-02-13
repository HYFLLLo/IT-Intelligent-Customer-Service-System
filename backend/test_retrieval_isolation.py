import requests
import json

# 测试不同问题的检索是否相互影响
def test_retrieval_isolation():
    # 测试问题1：Google Docs登录问题
    print("=== 测试问题1：Google Docs登录问题 ===")
    url = "http://localhost:8000/api/v1/employee/question"
    headers = {
        "Content-Type": "application/json"
    }
    data1 = {
        "question": "无法登录Google Docs账户；登录后无法打开文档文件",
        "category": "账户与权限管理"
    }
    
    response1 = requests.post(url, headers=headers, data=json.dumps(data1))
    print(f"响应状态码: {response1.status_code}")
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"回答: {result1.get('answer')[:200]}...")
        print(f"置信度: {result1.get('confidence')}")
    else:
        print(f"错误信息: {response1.text}")
    
    print("\n" + "-" * 80 + "\n")
    
    # 测试问题2：计算机无法开机问题
    print("=== 测试问题2：计算机无法开机问题 ===")
    data2 = {
        "question": "计算机在按下电源按钮后无法开机",
        "category": "硬件故障"
    }
    
    response2 = requests.post(url, headers=headers, data=json.dumps(data2))
    print(f"响应状态码: {response2.status_code}")
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"回答: {result2.get('answer')[:200]}...")
        print(f"置信度: {result2.get('confidence')}")
    else:
        print(f"错误信息: {response2.text}")
    
    print("\n" + "-" * 80 + "\n")
    
    # 测试问题3：网络连接问题
    print("=== 测试问题3：网络连接问题 ===")
    data3 = {
        "question": "无法连接到公司网络",
        "category": "网络连接"
    }
    
    response3 = requests.post(url, headers=headers, data=json.dumps(data3))
    print(f"响应状态码: {response3.status_code}")
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"回答: {result3.get('answer')[:200]}...")
        print(f"置信度: {result3.get('confidence')}")
    else:
        print(f"错误信息: {response3.text}")

if __name__ == "__main__":
    test_retrieval_isolation()
