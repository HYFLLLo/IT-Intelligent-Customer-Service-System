import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'test.db')
print(f"Database path: {db_path}")

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 查询所有反馈的完整信息
try:
    cursor.execute("""
        SELECT id, user_id, session_id, feedback_type, question_text, answer_text,
               issue_options, detailed_description, device_info, browser_info,
               feedback_submitted_at, is_read, is_processed
        FROM user_feedbacks;
    """)
    feedbacks = cursor.fetchall()
    print(f"Found {len(feedbacks)} feedbacks\n")
    
    for feedback in feedbacks:
        print(f"=== Feedback ID: {feedback['id']} ===")
        print(f"  feedback_type: '{feedback['feedback_type']}' (length: {len(feedback['feedback_type']) if feedback['feedback_type'] else 0})")
        print(f"  session_id: {feedback['session_id']}")
        print(f"  question_text: {feedback['question_text'][:50]}...")
        print(f"  issue_options: {feedback['issue_options']}")
        print(f"  detailed_description: {feedback['detailed_description']}")
        print(f"  is_read: {feedback['is_read']}")
        print(f"  is_processed: {feedback['is_processed']}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

conn.close()
