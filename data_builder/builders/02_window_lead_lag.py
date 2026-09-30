"""Builder for Category 02: 开窗函数 lead/lag"""

import random


def build(conn):
    cur = conn.cursor()
    # ===== stock_price 表：股票价格（波峰波谷） =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_price (
            id INTEGER,
            ds VARCHAR(20),
            price DOUBLE
        )
    """)

    random.seed(200)
    stock_data = []
    for stock_id in range(1, 4):
        base_price = random.uniform(50, 150)
        for day in range(1, 13):
            # 制造波峰波谷：正弦波动
            import math
            price = base_price + math.sin(day * 1.2) * random.uniform(8, 15) + random.uniform(-2, 2)
            stock_data.append((stock_id, f"2024-01-{day:02d}", round(price, 2)))

    cur.executemany("INSERT INTO stock_price (id, ds, price) VALUES (%s, %s, %s)", stock_data)

    # ===== data_table 表：前后列转换 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_table (
            id INTEGER,
            date VARCHAR(20),
            value DOUBLE
        )
    """)

    data_table_data = []
    for group_id in range(1, 4):
        base = random.uniform(10, 100)
        for day in range(1, 9):
            value = base + random.uniform(-10, 10)
            data_table_data.append((group_id, f"2024-02-{day:02d}", round(value, 2)))

    cur.executemany("INSERT INTO data_table (id, date, value) VALUES (%s, %s, %s)", data_table_data)

    # ===== metrics 表：变化率计算 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            date VARCHAR(20),
            value DOUBLE
        )
    """)

    metrics_data = []
    cur_val = 100.0
    for day in range(1, 16):
        cur_val += random.uniform(-15, 20)
        cur_val = max(10, cur_val)
        metrics_data.append((f"2024-03-{day:02d}", round(cur_val, 2)))

    cur.executemany("INSERT INTO metrics (date, value) VALUES (%s, %s)", metrics_data)

    print(f"     stock_price: {len(stock_data)} rows")
    print(f"     data_table: {len(data_table_data)} rows")
    print(f"     metrics: {len(metrics_data)} rows")
