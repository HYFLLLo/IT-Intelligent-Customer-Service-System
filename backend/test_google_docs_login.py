from app.config.settings import settings
import chromadb

# 初始化 Chroma 客户端
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)

# 获取知识库集合
collection = chroma_client.get_collection(name="it_knowledge_base")

# 获取所有文档
all_docs = collection.get()

# 处理返回结果
ids = all_docs.get("ids", [])
documents = all_docs.get("documents", [])
metadatas = all_docs.get("metadatas", [])

# 打印文档数量
print(f"总共获取到 {len(ids)} 个文档")

# 搜索包含 "Google Docs" 的文档
print("\n搜索包含 'Google Docs' 的文档:")
google_docs_docs = []
for i, doc in enumerate(documents):
    if "Google Docs" in doc or "google docs" in doc:
        google_docs_docs.append((i, doc))

if google_docs_docs:
    print(f"找到 {len(google_docs_docs)} 个包含 'Google Docs' 的文档:")
    for i, doc in google_docs_docs:
        print(f"文档 {i+1} 内容: {doc[:500]}...")
else:
    print("未找到包含 'Google Docs' 的文档")

# 搜索包含 "登录" 的文档
print("\n搜索包含 '登录' 的文档:")
login_docs = []
for i, doc in enumerate(documents):
    if "登录" in doc:
        login_docs.append((i, doc))

if login_docs:
    print(f"找到 {len(login_docs)} 个包含 '登录' 的文档:")
    for i, doc in login_docs[:5]:  # 只打印前5个
        print(f"文档 {i+1} 内容: {doc[:500]}...")
else:
    print("未找到包含 '登录' 的文档")

# 搜索包含 "文档" 和 "无法打开" 的文档
print("\n搜索包含 '文档' 和 '无法打开' 的文档:")
document_open_docs = []
for i, doc in enumerate(documents):
    if "文档" in doc and "无法打开" in doc:
        document_open_docs.append((i, doc))

if document_open_docs:
    print(f"找到 {len(document_open_docs)} 个包含 '文档' 和 '无法打开' 的文档:")
    for i, doc in document_open_docs:
        print(f"文档 {i+1} 内容: {doc[:500]}...")
else:
    print("未找到包含 '文档' 和 '无法打开' 的文档")
