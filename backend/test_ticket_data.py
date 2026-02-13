import os
import sys
import sqlite3

# 直接使用sqlite3连接数据库
db_path = "test.db"

print("=== 检查数据库中的工单数据 ===")

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有工单
cursor.execute("SELECT * FROM tickets")
tickets = cursor.fetchall()

print(f"共找到 {len(tickets)} 个工单")

for i, ticket in enumerate(tickets):
    print(f"\n工单 {i+1}:")
    print(f"ID: {ticket['id']}")
    print(f"标题: {ticket['title']}")
    print(f"内容: {ticket['content'][:100]}...")
    print(f"状态: {ticket['status']}")
    print(f"优先级: {ticket['priority']}")
    print(f"类别: {ticket['category']}")
    print(f"创建时间: {ticket['created_at']}")
    print(f"更新时间: {ticket['updated_at']}")

# 检查数据库连接编码
print("\n=== 检查数据库编码 ===")
cursor.execute("PRAGMA encoding;")
encoding = cursor.fetchone()[0]
print(f"SQLite 编码: {encoding}")

# 测试插入中文数据
print("\n=== 测试插入中文数据 ===")
try:
    cursor.execute('''
        INSERT INTO tickets (title, content, status, priority, user_id, category, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "测试中文标题",
        "测试中文内容，看看是否能正常存储和显示",
        "pending",
        "medium",
        1,
        "technical",
        "2024-01-01T00:00:00",
        "2024-01-01T00:00:00"
    ))
    conn.commit()
    
    # 查询刚插入的工单
    cursor.execute("SELECT * FROM tickets WHERE title = ?", ("测试中文标题",))
    test_ticket = cursor.fetchone()
    if test_ticket:
        print(f"插入测试工单成功，ID: {test_ticket['id']}")
        print(f"标题: {test_ticket['title']}")
        print(f"内容: {test_ticket['content']}")
    else:
        print("插入测试工单成功，但无法查询到")
except Exception as e:
    print(f"插入测试工单失败: {e}")
    conn.rollback()

# 关闭数据库连接
cursor.close()
conn.close()

print("\n测试完成")
