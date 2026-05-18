#!/usr/bin/env python3
"""
北京交通大学智慧食堂实时监测系统 - 后端服务
使用 Python Flask + SQLite 实现
"""

from flask import Flask, jsonify, send_file
from flask_cors import CORS
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 数据库文件名
DB_NAME = 'canteen.db'

def get_random_queue():
    """生成随机排队人数 (1-15人)"""
    return random.randint(1, 15)

def calculate_wait_time(queue_count):
    """计算预计等待时间"""
    if queue_count <= 2:
        return "无需排队"
    elif queue_count <= 5:
        return f"{queue_count * 1.5:.0f}min"
    elif queue_count <= 10:
        return f"{queue_count * 1.2:.0f}min"
    else:
        return f"{queue_count * 1.5:.0f}min"

@app.route('/api/windows', methods=['GET'])
def get_windows():
    """获取窗口实时数据（从数据库读取并更新）"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 更新数据
    c.execute('SELECT id FROM windows')
    window_ids = [row[0] for row in c.fetchall()]
    
    for wid in window_ids:
        queue_count = get_random_queue()
        wait_time = calculate_wait_time(queue_count)
        status = 'open' if random.random() > 0.1 else 'closed'
        c.execute('''
            UPDATE windows SET queue_count=?, wait_time=?, status=?, last_update=? WHERE id=?
        ''', (queue_count, wait_time, status, datetime.now().isoformat(), wid))
    
    # 查询数据
    c.execute('SELECT id, name, category, queue_count, wait_time, status FROM windows')
    windows = []
    for row in c.fetchall():
        windows.append({
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "queueCount": row[3],
            "waitTime": row[4],
            "status": row[5]
        })
    
    conn.commit()
    conn.close()
    return jsonify(windows)

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """获取餐桌实时数据（从数据库读取并更新）"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 更新数据
    c.execute('SELECT id FROM tables')
    table_ids = [row[0] for row in c.fetchall()]
    
    for tid in table_ids:
        is_occupied = 1 if random.random() > 0.4 else 0
        current_people = random.randint(1, 4) if is_occupied else 0
        c.execute('''
            UPDATE tables SET is_occupied=?, current_people=?, last_update=? WHERE id=?
        ''', (is_occupied, current_people, datetime.now().isoformat(), tid))
    
    # 查询数据
    c.execute('SELECT id, is_occupied, capacity, current_people FROM tables')
    tables = []
    for row in c.fetchall():
        tables.append({
            "id": row[0],
            "isOccupied": bool(row[1]),
            "capacity": row[2],
            "currentPeople": row[3],
            "lastUpdate": datetime.now().isoformat()
        })
    
    conn.commit()
    conn.close()
    return jsonify(tables)

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取食堂统计数据"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM tables WHERE is_occupied=1')
    occupied_tables = c.fetchone()[0]
    
    c.execute('SELECT SUM(current_people) FROM tables')
    total_people = c.fetchone()[0] or 0
    
    c.execute('SELECT AVG(queue_count) FROM windows WHERE status="open"')
    avg_queue = c.fetchone()[0] or 0
    
    conn.close()
    
    return jsonify({
        "totalTables": 80,
        "occupiedTables": occupied_tables,
        "emptyTables": 80 - occupied_tables,
        "totalPeople": total_people,
        "avgWaitTime": int(avg_queue * 1.2),
        "peakTime": "12:00-12:30",
        "updateTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """获取今日菜单"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 更新销量
    c.execute('SELECT id, sold FROM menu')
    for row in c.fetchall():
        new_sold = max(0, row[1] + random.randint(-5, 10))
        c.execute('UPDATE menu SET sold=? WHERE id=?', (new_sold, row[0]))
    
    # 查询菜单
    c.execute('SELECT id, name, price, rating, sold FROM menu')
    menu = []
    for row in c.fetchall():
        menu.append({
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "rating": row[3],
            "sold": row[4]
        })
    
    conn.commit()
    conn.close()
    return jsonify(menu)

@app.route('/')
def index():
    """返回首页"""
    return send_file('index.html')

if __name__ == '__main__':
    # 确保数据库存在
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.close()
    except:
        print("数据库文件不存在，请先运行 init_database.py")
        exit(1)
    
    print("Server running on http://localhost:8888")
    print("Database file:", DB_NAME)
    print("API endpoints:")
    print("  GET /api/windows - 窗口排队数据")
    print("  GET /api/tables - 餐桌占用数据")
    print("  GET /api/statistics - 食堂统计数据")
    print("  GET /api/menu - 今日菜单")
    app.run(host='0.0.0.0', port=8888, debug=True)