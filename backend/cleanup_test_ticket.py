import sqlite3

# 连接数据库
db_path = "test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 删除测试工单 ===")

# 删除标题为"测试中文标题"的工单
cursor.execute("DELETE FROM tickets WHERE title = ?", ("测试中文标题",))
conn.commit()

print(f"已删除 {cursor.rowcount} 个测试工单")

# 重新查询所有工单
cursor.execute("SELECT * FROM tickets")
tickets = cursor.fetchall()

print(f"\n删除后剩余 {len(tickets)} 个工单")

# 关闭数据库连接
cursor.close()
conn.close()

print("\n清理完成")
