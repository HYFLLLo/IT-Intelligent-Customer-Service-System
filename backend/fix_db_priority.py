import sqlite3

# 修复数据库中的优先级值格式，使其与Enum定义一致
def fix_db_priority():
    print("=== 修复数据库优先级值格式 ===")
    
    db_path = "test.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 更新优先级值为大写
        cursor.execute("UPDATE tickets SET priority = 'LOW' WHERE priority LIKE '%low%'")
        cursor.execute("UPDATE tickets SET priority = 'MEDIUM' WHERE priority LIKE '%medium%'")
        cursor.execute("UPDATE tickets SET priority = 'HIGH' WHERE priority LIKE '%high%'")
        cursor.execute("UPDATE tickets SET priority = 'URGENT' WHERE priority LIKE '%urgent%'")
        
        # 提交更改
        conn.commit()
        
        # 验证修复结果
        cursor.execute("SELECT id, title, priority FROM tickets")
        tickets = cursor.fetchall()
        
        print(f"修复完成，共更新 {cursor.rowcount} 条记录")
        print("\n修复后的工单优先级:")
        
        for i, ticket in enumerate(tickets):
            print(f"工单 {i+1}: ID={ticket[0]}, 标题={ticket[1]}, 优先级={ticket[2]}")
        
        conn.close()
        
        print("\n数据库优先级值修复成功！")
        
    except Exception as e:
        print(f"修复失败: {str(e)}")

if __name__ == "__main__":
    fix_db_priority()
