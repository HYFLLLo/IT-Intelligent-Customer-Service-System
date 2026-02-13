import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 检查数据库编码
cursor.execute('PRAGMA encoding;')
encoding = cursor.fetchone()
print('SQLite database encoding:', encoding)

# 测试插入和读取中文字符
cursor.execute('''
CREATE TABLE IF NOT EXISTS test_encoding (
    id INTEGER PRIMARY KEY,
    text TEXT
)
''')

# 插入中文字符
cursor.execute('INSERT INTO test_encoding (text) VALUES (?)', ('测试中文字符',))
conn.commit()

# 读取中文字符
cursor.execute('SELECT text FROM test_encoding')
result = cursor.fetchone()
print('Retrieved text:', result[0])

# 清理测试表
cursor.execute('DROP TABLE test_encoding')
conn.commit()

# 关闭连接
conn.close()