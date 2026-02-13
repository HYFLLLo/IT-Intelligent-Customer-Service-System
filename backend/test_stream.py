import requests
import time

# 测试流式API
url = "http://localhost:8000/api/v1/employee/question/stream"
headers = {"Content-Type": "application/json"}
data = {"question": "如何重置密码？"}

print("测试流式API...")
try:
    response = requests.post(url, headers=headers, json=data, stream=True)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print("开始接收流式数据...")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"接收到: {decoded_line}")
                time.sleep(0.1)  # 模拟延迟
    else:
        print(f"错误响应: {response.text}")
except Exception as e:
    print(f"错误: {str(e)}")
