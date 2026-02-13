import sqlite3

# 检查数据库中优先级字段的实际存储格式
def check_db_priority():
    print("=== 检查数据库优先级字段格式 ===")
    
    db_path = "test.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有工单的优先级
        cursor.execute("SELECT id, title, priority FROM tickets")
        tickets = cursor.fetchall()
        
        print(f"共找到 {len(tickets)} 个工单")
        print("\n工单优先级详情:")
        
        for i, ticket in enumerate(tickets):
            priority_value = ticket['priority']
            print(f"工单 {i+1}: ID={ticket['id']}, 标题={ticket['title']}, 优先级='{priority_value}', 类型={type(priority_value)}")
            print(f"   优先级长度: {len(priority_value)}")
            print(f"   优先级大写: '{priority_value.upper()}'")
            print(f"   优先级小写: '{priority_value.lower()}'")
        
        # 检查优先级字段的不同值
        cursor.execute("SELECT DISTINCT priority FROM tickets")
        distinct_priorities = cursor.fetchall()
        
        print("\n数据库中存在的优先级值:")
        for priority in distinct_priorities:
            print(f"   '{priority[0]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_db_priority()
