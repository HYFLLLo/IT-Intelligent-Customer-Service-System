import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(__file__), "test.db")

print(f"数据库路径: {db_path}")
print(f"数据库文件是否存在: {os.path.exists(db_path)}")

def fix_knowledge_encoding():
    """修复知识库编码问题"""
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查knowledge_documents表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_documents';")
        if not cursor.fetchone():
            print("knowledge_documents表不存在")
            return
        
        # 检查knowledge_categories表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_categories';")
        if not cursor.fetchone():
            print("knowledge_categories表不存在")
            return
        
        # 查询所有知识库文章
        cursor.execute("SELECT id, title, content, category_id, created_at FROM knowledge_documents;")
        knowledge_list = cursor.fetchall()
        
        print(f"\n找到 {len(knowledge_list)} 篇知识库文章")
        
        # 标记需要删除的乱码文章
        to_delete = []
        
        for item in knowledge_list:
            id = item['id']
            title = item['title']
            content = item['content']
            
            print(f"\n文章ID: {id}")
            print(f"标题: {title}")
            print(f"内容预览: {content[:100]}...")
            
            # 检查是否包含乱码（??）
            if '??' in title or '??' in content:
                print(f"⚠️  发现乱码，标记为删除")
                to_delete.append(id)
            else:
                print("✅  内容正常")
        
        # 删除乱码文章
        if to_delete:
            print(f"\n准备删除 {len(to_delete)} 篇乱码文章")
            
            for id in to_delete:
                try:
                    cursor.execute("DELETE FROM knowledge_documents WHERE id = ?;", (id,))
                    print(f"✅  删除文章ID: {id}")
                except Exception as e:
                    print(f"❌ 删除文章ID {id} 失败: {str(e)}")
            
            # 提交更改
            conn.commit()
            print(f"\n✅  成功删除 {len(to_delete)} 篇乱码文章")
        else:
            print("\n✅  没有发现乱码文章")
        
        # 查询所有分类
        cursor.execute("SELECT id, name, description FROM knowledge_categories;")
        categories = cursor.fetchall()
        
        print(f"\n找到 {len(categories)} 个分类")
        for category in categories:
            id = category['id']
            name = category['name']
            print(f"分类ID: {id}, 名称: {name}")
            
            # 检查分类是否包含乱码
            if '??' in name:
                print(f"⚠️  发现乱码分类，标记为删除")
                # 删除分类
                try:
                    cursor.execute("DELETE FROM knowledge_categories WHERE id = ?;", (id,))
                    print(f"✅  删除分类ID: {id}")
                except Exception as e:
                    print(f"❌ 删除分类ID {id} 失败: {str(e)}")
        
        # 提交更改
        conn.commit()
        
        # 再次查询确认
        cursor.execute("SELECT id, title FROM knowledge_documents;")
        remaining = cursor.fetchall()
        print(f"\n清理后剩余 {len(remaining)} 篇知识库文章")
        for item in remaining:
            print(f"文章ID: {item['id']}, 标题: {item['title']}")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n✅  数据库连接已关闭")

if __name__ == "__main__":
    fix_knowledge_encoding()
