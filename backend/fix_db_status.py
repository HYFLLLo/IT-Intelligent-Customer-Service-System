import sqlite3

# 修复数据库中的状态值格式，使其与Enum定义一致
def fix_db_status():
    print("=== 修复数据库状态值格式 ===")
    
    db_path = "test.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 更新状态值为大写
        cursor.execute("UPDATE tickets SET status = 'PENDING' WHERE status LIKE '%pending%'")
        cursor.execute("UPDATE tickets SET status = 'CLOSED' WHERE status LIKE '%closed%'")
        cursor.execute("UPDATE tickets SET status = 'PROCESSING' WHERE status LIKE '%processing%'")
        cursor.execute("UPDATE tickets SET status = 'RESOLVED' WHERE status LIKE '%resolved%'")
        cursor.execute("UPDATE tickets SET status = 'REOPENED' WHERE status LIKE '%reopened%'")
        
        # 提交更改
        conn.commit()
        
        # 验证修复结果
        cursor.execute("SELECT id, title, status FROM tickets")
        tickets = cursor.fetchall()
        
        print(f"修复完成，共更新 {cursor.rowcount} 条记录")
        print("\n修复后的工单状态:")
        
        for i, ticket in enumerate(tickets):
            print(f"工单 {i+1}: ID={ticket[0]}, 标题={ticket[1]}, 状态={ticket[2]}")
        
        conn.close()
        
        print("\n数据库状态值修复成功！")
        
    except Exception as e:
        print(f"修复失败: {str(e)}")

if __name__ == "__main__":
    fix_db_status()
