import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
print(f"Database path: {db_path}")

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
cursor = conn.cursor()

# 查询反馈表
try:
    cursor.execute("SELECT id, feedback_type, question_text, feedback_submitted_at FROM user_feedbacks;")
    feedbacks = cursor.fetchall()
    print(f"Found {len(feedbacks)} feedbacks")
    print("\n=== All feedback types ===")
    for feedback in feedbacks:
        print(f"ID: {feedback['id']}, Type: '{feedback['feedback_type']}', Question: {feedback['question_text'][:30]}...")
    
    # 统计
    print("\n=== Statistics ===")
    cursor.execute("SELECT feedback_type, COUNT(*) as count FROM user_feedbacks GROUP BY feedback_type;")
    stats = cursor.fetchall()
    for stat in stats:
        print(f"Type: '{stat['feedback_type']}', Count: {stat['count']}")
        
except Exception as e:
    print(f"Error querying feedbacks: {e}")
    import traceback
    traceback.print_exc()

# 关闭连接
conn.close()
