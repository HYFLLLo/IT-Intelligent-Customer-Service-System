import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Chroma数据库配置
    CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chromadb")))
    
    # LLM配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # 认证配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # 应用配置
    APP_NAME: str = "IT Intelligent Customer Service System"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()