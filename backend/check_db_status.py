import sqlite3

# 检查数据库中状态字段的实际存储格式
def check_db_status():
    print("=== 检查数据库状态字段格式 ===")
    
    db_path = "test.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有工单的状态
        cursor.execute("SELECT id, title, status FROM tickets")
        tickets = cursor.fetchall()
        
        print(f"共找到 {len(tickets)} 个工单")
        print("\n工单状态详情:")
        
        for i, ticket in enumerate(tickets):
            status_value = ticket['status']
            print(f"工单 {i+1}: ID={ticket['id']}, 标题={ticket['title']}, 状态='{status_value}', 类型={type(status_value)}")
            print(f"   状态长度: {len(status_value)}")
            print(f"   状态大写: '{status_value.upper()}'")
            print(f"   状态小写: '{status_value.lower()}'")
        
        # 检查状态字段的不同值
        cursor.execute("SELECT DISTINCT status FROM tickets")
        distinct_statuses = cursor.fetchall()
        
        print("\n数据库中存在的状态值:")
        for status in distinct_statuses:
            print(f"   '{status[0]}'")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_db_status()
