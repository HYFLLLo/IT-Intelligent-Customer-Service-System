# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.v1 import router as v1_router
from fastapi.responses import JSONResponse
import json

# 导入所有模型以确保创建数据库表
from app.models.user import User
from app.models.ticket import Ticket, TicketResponse
from app.models.knowledge import KnowledgeCategory, KnowledgeDocument
from app.models.quality import QualityCheck, QualityRule
from app.models.question import QuestionHistory
from app.models.feedback import UserFeedback, FeedbackSession
from app.models.analytics import AnalyticsEvent, AnalyticsDailyStats

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(v1_router, prefix="/api/v1")

# 自定义JSONResponse，确保使用UTF-8编码
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json"
    
    def render(self, content):
        return json.dumps(
            content,
            ensure_ascii=False,  # 确保中文字符不被转义
            indent=None,
            separators=(",", ":")
        ).encode("utf-8")

# 替换默认的JSONResponse
app.response_class = UTF8JSONResponse

@app.get('/')
def read_root():
    return {'message': 'IT Intelligent Customer Service System Backend'}

@app.get('/health')
def health_check():
    return {'status': 'healthy'}

@app.get('/test-encoding')
def test_encoding():
    return {'message': '测试编码，中文字符是否正常显示'}

