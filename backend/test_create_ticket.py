import requests
import json

# 测试创建工单，使用中文字符
test_data = {
    "title": "测试工单，中文标题",
    "description": "这是一个测试工单，使用中文描述来测试字符编码是否正常",
    "priority": "medium",
    "user": "测试用户",
    "department": "测试部门",
    "category": "technical"
}

# 发送请求
response = requests.post(
    'http://localhost:8000/api/v1/employee/ticket',
    headers={
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
    },
    data=json.dumps(test_data, ensure_ascii=False).encode('utf-8')
)

# 打印响应结果
print(f"Status code: {response.status_code}")
print(f"Response: {response.json()}")

# 查询通知列表
response = requests.get('http://localhost:8000/api/v1/employee/notifications')
data = response.json()
print("\n通知列表:")
print(json.dumps(data, ensure_ascii=False, indent=2))