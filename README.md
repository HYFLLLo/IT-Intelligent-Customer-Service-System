# IT Intelligent Customer Service System (Enterprise Edition)

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal)
![License](https://img.shields.io/badge/license-MIT-orange)

**AI深度赋能的IT服务中枢**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [项目结构](#-项目结构) • [API文档](#-api文档)

</div>

---

## 📌 项目简介

企业级IT智能客服系统，通过AI技术实现"员工自助解决80%常见问题 + 坐席效率提升50% + 服务质量可量化"的三位一体目标。

### 核心价值

| 维度 | 价值点 | 量化目标 |
|------|--------|----------|
| **员工体验** | 7×24小时秒级响应，减少等待焦虑 | 常见问题解决率≥85% |
| **坐席提效** | AI辅助生成回复/提取字段，减少重复劳动 | 单工单处理时长↓40% |
| **质检能力** | 全流程数据留痕，质检自动化 | 人工质检工作量↓70% |
| **知识沉淀** | 问答数据反哺知识库，持续进化 | 知识库月度更新率≥15% |

---

## ✨ 功能特性

### 员工端
- 🔍 **智能问答**：基于RAG技术的7×24小时智能问答
- 📝 **工单提交**：一键提交IT问题工单
- 📊 **进度跟踪**：实时查看工单处理状态
- 💬 **历史记录**：查看历史会话和工单记录

### 坐席端
- 📋 **工单看板**：直观的仪表盘展示待处理工单
- 🤖 **AI回复建议**：智能生成回复建议，提升处理效率
- 📦 **字段自动提取**：自动提取设备型号、系统版本等关键信息
- ✅ **质检报告**：查看服务质量评分和改进建议

### AI能力中心
- 🔎 **知识检索+生成（RAG）**：混合检索（向量+关键词）
- 📌 **工单字段提取**：基于DeepSeek Function Calling
- 🎯 **回复内容质检**：规则引擎+AI评分（1-5分）
- 📚 **知识库管理**：支持PDF/Word文档解析

---

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+ (前端开发)
- SQLite 3
- DeepSeek API Key

### 后端安装

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息

# 初始化数据库
python init_db.py

# 启动服务
python main.py
```

后端服务将在 `http://localhost:8000` 启动

### 前端安装

```bash
# 进入前端目录（如果存在）
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 验证安装

访问以下地址验证服务是否正常运行：

- 后端健康检查：http://localhost:8000/health
- API文档：http://localhost:8000/docs

---

## 🏗️ 技术架构

### 系统架构图

```
┌─────────────┐     ┌───────────────────────────────────────────────────────┐
│   前端层     │     │                   后端服务层                          │
│             │     │                                                       │
│ • 员工端     │────▶│ • API网关（认证/限流）                                │
│ • 坐席端     │────▶│ • 智能问答服务（RAG引擎）                             │
│ (Vue3+TS)   │     │ • 工单工作流引擎                                      │
│             │     │ • AI能力中心（字段提取/质检）                         │
└─────────────┘     └───────────────────────────────────────────────────────┘
                              │               │                │
                              ▼               ▼                ▼
                    ┌─────────────┐   ┌──────────────┐  ┌──────────────┐
                    │  SQLite     │   │ 向量数据库    │  │ DeepSeek API │
                    │ (业务数据)   │   │ (Chroma)     │  │ (大模型服务)  │
                    └─────────────┘   └──────────────┘  └──────────────┘
```

### 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | Vue3 + TypeScript + Element Plus + Pinia | 组合式API、类型安全、企业级组件 |
| **后端** | FastAPI + SQLAlchemy + SQLite | 异步高性能、ORM、轻量级数据库 |
| **AI层** | DeepSeek API + Chroma | 中文理解强、向量数据库 |
| **其他** | Uvicorn + Pydantic + JWT | ASGI服务器、数据验证、身份认证 |

---

## 📁 项目结构

```
backend/
├── app/
│   ├── api/v1/          # API路由
│   │   ├── admin/       # 管理员接口
│   │   ├── agent/       # 坐席接口
│   │   ├── auth/        # 认证接口
│   │   ├── employee/    # 员工接口
│   │   ├── analytics.py # 数据分析
│   │   └── feedback.py  # 反馈接口
│   ├── config/          # 配置文件
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   │   ├── auth/        # 认证服务
│   │   ├── rag/         # RAG服务
│   │   └── ticket/      # 工单服务
│   └── websocket/       # WebSocket接口
├── chroma_db/           # 向量数据库
├── main.py              # 应用入口
├── requirements.txt     # Python依赖
└── .env.example         # 环境变量示例
```

---

## 🔌 API文档

启动后端服务后，访问以下地址查看完整的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/tickets` | POST | 创建工单 |
| `/api/v1/tickets/{id}` | GET | 获取工单详情 |
| `/api/v1/qa/ask` | POST | 智能问答 |
| `/api/v1/feedback` | POST | 提交反馈 |
| `/api/v1/analytics` | GET | 获取统计数据 |

---

## 📊 数据模型

### 核心数据表

- **User**: 用户信息（员工、坐席、管理员）
- **Ticket**: 工单信息
- **TicketResponse**: 工单回复记录
- **KnowledgeCategory**: 知识库分类
- **KnowledgeDocument**: 知识库文档
- **QualityCheck**: 质检记录
- **UserFeedback**: 用户反馈
- **AnalyticsEvent**: 分析事件

---

## 🎯 成功度量标准

| 维度 | 指标 | 目标值 |
|------|------|--------|
| **业务效果** | 常见问题自助解决率 | ≥85% |
| **坐席效率** | 平均单工单处理时长 | ↓40% |
| **服务质量** | 工单一次解决率 | ≥90% |
| **系统健康** | 服务可用性 | ≥99.5% |

---

## 🛠️ 开发指南

### 添加新的API端点

1. 在 `app/api/v1/` 下创建或编辑路由文件
2. 在 `app/models/` 下定义数据模型
3. 在 `app/services/` 下实现业务逻辑
4. 在 `app/api/v1/__init__.py` 中注册路由

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test_api.py

# 查看测试覆盖率
pytest --cov=app
```

---

## 📝 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```env
# 数据库配置
DATABASE_URL=sqlite:///./customer_service.db

# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com

# JWT配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📮 联系方式

- 项目地址：https://github.com/HYFLLLo/IT-Intelligent-Customer-Service-System
- 问题反馈：[GitHub Issues](https://github.com/HYFLLLo/IT-Intelligent-Customer-Service-System/issues)

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐️ Star**

Made with ❤️ by HYFLLLo

</div>
