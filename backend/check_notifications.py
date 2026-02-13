from app.database import get_db
from app.models.user import Notification

db = next(get_db())
try:
    notifications = db.query(Notification).filter(Notification.user_id == 1).all()
    print(f'获取到 {len(notifications)} 条通知')
except Exception as e:
    print(f'错误: {str(e)}')
finally:
    db.close()