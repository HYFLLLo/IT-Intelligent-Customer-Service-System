import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
print(f"Database path: {db_path}")

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 修复 feedback_type 为空的记录
try:
    # 查找所有 feedback_type 为空字符串的记录
    cursor.execute("SELECT id, issue_options FROM user_feedbacks WHERE feedback_type = '';")
    empty_records = cursor.fetchall()
    
    print(f"Found {len(empty_records)} records with empty feedback_type")
    
    for record in empty_records:
        record_id = record[0]
        issue_options = record[1]
        
        # 如果有 issue_options，说明是不满意反馈
        if issue_options:
            new_type = 'dissatisfied'
        else:
            new_type = 'satisfied'
        
        # 更新记录
        cursor.execute(
            "UPDATE user_feedbacks SET feedback_type = ? WHERE id = ?;",
            (new_type, record_id)
        )
        print(f"Updated record {record_id}: feedback_type = '{new_type}' (issue_options: {issue_options})")
    
    # 提交更改
    conn.commit()
    print("\n修复完成!")
    
    # 验证修复结果
    cursor.execute("SELECT id, feedback_type, issue_options FROM user_feedbacks;")
    all_records = cursor.fetchall()
    print("\n=== 修复后的所有记录 ===")
    for record in all_records:
        print(f"ID: {record[0]}, Type: '{record[1]}', Issues: {record[2]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()

conn.close()
