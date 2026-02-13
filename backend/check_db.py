import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
print(f"Database path: {db_path}")

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
cursor = conn.cursor()

# 查询工单表
try:
    cursor.execute("SELECT id, title, content FROM tickets LIMIT 10;")
    tickets = cursor.fetchall()
    print(f"Found {len(tickets)} tickets")
    for ticket in tickets:
        print(f"Ticket ID: {ticket['id']}")
        print(f"Title: {ticket['title']}")
        print(f"Content: {ticket['content']}")
        print("---")
except Exception as e:
    print(f"Error querying tickets: {e}")

# 查询通知表
try:
    cursor.execute("SELECT id, title, content, response FROM notifications LIMIT 10;")
    notifications = cursor.fetchall()
    print(f"Found {len(notifications)} notifications")
    for notification in notifications:
        print(f"Notification ID: {notification['id']}")
        print(f"Title: {notification['title']}")
        print(f"Content: {notification['content']}")
        print(f"Response: {notification['response']}")
        print("---")
except Exception as e:
    print(f"Error querying notifications: {e}")

# 关闭连接
conn.close()