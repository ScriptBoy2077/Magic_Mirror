import sqlite3


def get_recent_readings(limit = None):
    if limit is None:
        limit = 3
        
    conn = sqlite3.connect("sensor_data.db")
    conn.row_factory = sqlite3.Row  # 使返回结果为字典形式
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM sensor_readings 
    ORDER BY timestamp DESC 
    LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为字典列表
    result = []
    for row in rows:
        row_dict = dict(row)
        result.append(row_dict)
    
    return result


if __name__ == "__main__":
    temp = get_recent_readings(1)
    print(f"今日气温{temp[0]['temperature']}, 湿度{temp[0]['humidity']}")