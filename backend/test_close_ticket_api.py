import requests
import json

# 测试关闭工单
def test_close_ticket(ticket_id):
    url = f"http://localhost:8000/api/v1/agent/tickets/{ticket_id}/close"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "reply_content": "已解决您的 Google Docs 登录问题，建议您清除浏览器缓存和 Cookie，然后重新尝试登录。",
        "skip_quality_check": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"=== 测试关闭工单 #{ticket_id} ===")
    print(f"响应状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 关闭工单成功:")
        print(f"   消息: {result.get('message')}")
        print(f"   工单ID: {result.get('ticket_id')}")
        return True
    else:
        print(f"❌ 关闭工单失败:")
        print(f"   错误信息: {response.text}")
        return False

if __name__ == "__main__":
    ticket_id = 2  # 使用刚刚创建的工单ID
    test_close_ticket(ticket_id)
