import sqlite3

# 详细检查数据库中所有工单的优先级值
def check_all_priorities():
    print("=== 详细检查所有工单优先级 ===")
    
    db_path = "test.db"
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有工单的详细信息
        cursor.execute("SELECT id, title, status, priority FROM tickets")
        tickets = cursor.fetchall()
        
        print(f"共找到 {len(tickets)} 个工单")
        print("\n所有工单详情:")
        
        for i, ticket in enumerate(tickets):
            print(f"工单 {i+1}:")
            print(f"   ID: {ticket['id']}")
            print(f"   标题: {ticket['title']}")
            print(f"   状态: '{ticket['status']}'")
            print(f"   优先级: '{ticket['priority']}'")
            print(f"   优先级类型: {type(ticket['priority'])}")
            print(f"   优先级ASCII: {[ord(c) for c in ticket['priority']]}")
        
        # 检查是否有小写的优先级值
        cursor.execute("SELECT id, title, priority FROM tickets WHERE priority NOT IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')")
        invalid_priorities = cursor.fetchall()
        
        if invalid_priorities:
            print("\n发现无效的优先级值:")
            for ticket in invalid_priorities:
                print(f"   ID={ticket['id']}, 标题={ticket['title']}, 优先级='{ticket['priority']}'")
        else:
            print("\n所有优先级值都是有效的！")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_all_priorities()
