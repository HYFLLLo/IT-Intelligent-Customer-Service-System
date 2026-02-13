import sqlite3

# 连接到SQLite数据库
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 查询tickets表中的数据
cursor.execute('SELECT id, title, content, category FROM tickets')
tickets = cursor.fetchall()

print('Total tickets:', len(tickets))
for ticket in tickets:
    print('ID:', ticket[0])
    print('Title:', ticket[1])
    print('Content:', ticket[2])
    print('Category:', ticket[3])
    print('---')

# 关闭连接
conn.close()