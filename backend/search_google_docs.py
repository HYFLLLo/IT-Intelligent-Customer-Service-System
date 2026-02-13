from app.services.rag.document_processor import DocumentProcessor
from app.services.rag.retriever import Retriever

# 初始化文档处理器
processor = DocumentProcessor()
collection = processor.collection

# 获取所有文档
all_docs = collection.get()

# 搜索包含 "Google Docs" 的文档
print("搜索包含 'Google Docs' 的文档:")
google_docs_docs = []
for i, doc in enumerate(all_docs.get('documents', [])):
    if 'Google Docs' in doc or 'google docs' in doc:
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
for i, doc in enumerate(all_docs.get('documents', [])):
    if '登录' in doc:
        login_docs.append((i, doc))

if login_docs:
    print(f"找到 {len(login_docs)} 个包含 '登录' 的文档:")
    for i, doc in login_docs[:3]:  # 只显示前3个
        print(f"文档 {i+1} 内容: {doc[:500]}...")
else:
    print("未找到包含 '登录' 的文档")
