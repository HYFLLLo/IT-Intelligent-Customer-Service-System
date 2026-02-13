import requests
import json

# 测试创建工单
def test_create_ticket():
    url = "http://localhost:8000/api/v1/employee/ticket"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "title": "测试工单：Google Docs登录问题",
        "description": "用户无法在Google Docs账户中登录；登录后无法打开文档文件",
        "priority": "medium",
        "category": "账户与权限管理",
        "user": "测试用户",
        "department": "测试部门"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print("=== 测试创建工单 ===")
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        ticket_data = response.json()
        print(f"✅ 创建工单成功:")
        print(f"   工单ID: {ticket_data.get('id')}")
        print(f"   工单标题: {ticket_data.get('title')}")
        return ticket_data.get('id')
    else:
        print(f"❌ 创建工单失败:")
        print(f"   错误信息: {response.text}")
        return None

if __name__ == "__main__":
    ticket_id = test_create_ticket()
    print(f"\n创建的工单ID: {ticket_id}")
