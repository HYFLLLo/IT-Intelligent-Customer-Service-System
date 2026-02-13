import requests
import json

# 测试员工端智能问答API
url = "http://localhost:8000/api/v1/employee/question"
headers = {"Content-Type": "application/json"}
data = {"question": "如何重置密码？"}

print("测试API调用...")
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
except Exception as e:
    print(f"错误: {str(e)}")
