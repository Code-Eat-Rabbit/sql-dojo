"""Builder for Category 04: 累计汇总"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== user_visits 表：累计访问次数 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_visits (
            user_id INTEGER,
            month_id TEXT,
            visit_cnt_1m INTEGER
        )
    """)

    random.seed(400)
    user_visits_data = []
    for user_id in range(1, 6):
        for month in range(1, 13):
            visits = random.randint(1, 30)
            user_visits_data.append((user_id, f"2024-{month:02d}", visits))

    conn.executemany("INSERT INTO user_visits (user_id, month_id, visit_cnt_1m) VALUES (?, ?, ?)", user_visits_data)

    # ===== live_log 表：直播间进出日志 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_log (
            room_id INTEGER,
            user_id INTEGER,
            login_time TEXT,
            logout_time TEXT
        )
    """)

    live_log_data = []
    for room_id in range(1, 3):
        for user_id in range(1, 11):
            # 登录时间
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            login = f"2022-05-01 {hour:02d}:{minute:02d}:{second:02d}"

            # 在线时长 10-120 分钟
            duration = random.randint(10, 120)
            total_min = hour * 60 + minute + duration
            out_hour = (total_min // 60) % 24
            out_min = total_min % 60
            logout = f"2022-05-01 {out_hour:02d}:{out_min:02d}:{random.randint(0, 59):02d}"

            live_log_data.append((room_id, user_id, login, logout))

            # 额外添加一些 20210310 的数据给 04_02 使用
            hour2 = random.randint(8, 20)
            minute2 = random.randint(0, 59)
            login2 = f"2021-03-10 {hour2:02d}:{minute2:02d}:00"
            dur2 = random.randint(10, 60)
            out_h2 = (hour2 * 60 + minute2 + dur2) // 60 % 24
            out_m2 = (hour2 * 60 + minute2 + dur2) % 60
            logout2 = f"2021-03-10 {out_h2:02d}:{out_m2:02d}:00"
            live_log_data.append((room_id, user_id + 10, login2, logout2))

    conn.executemany("INSERT INTO live_log (room_id, user_id, login_time, logout_time) VALUES (?, ?, ?, ?)", live_log_data)

    # ===== user_spend 表：用户累计消费达到1000元 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_spend (
            user_id INTEGER,
            dt TEXT,
            price REAL
        )
    """)

    user_spend_data = []
    for user_id in range(1, 5):
        for day in range(1, 21):
            price = random.uniform(20, 200)
            user_spend_data.append((user_id, f"2024-03-{day:02d}", round(price, 2)))

    conn.executemany("INSERT INTO user_spend (user_id, dt, price) VALUES (?, ?, ?)", user_spend_data)

    # ===== orders 表：商品复购 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            user_id INTEGER,
            product_id TEXT,
            order_id TEXT
        )
    """)

    orders_data = []
    order_counter = 1
    for user_id in range(1, 6):
        products = ["P001", "P002", "P003", "P004"]
        # 每个用户随机购买3-8个订单
        for _ in range(random.randint(3, 8)):
            pid = random.choice(products)
            orders_data.append((user_id, pid, f"ORD{order_counter:04d}"))
            order_counter += 1

    conn.executemany("INSERT INTO orders (user_id, product_id, order_id) VALUES (?, ?, ?)", orders_data)

    # ===== product_price 表：历史新低 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS product_price (
            id INTEGER,
            ds TEXT,
            price REAL
        )
    """)

    product_price_data = []
    for pid in range(1, 4):
        base = random.uniform(50, 200)
        for day in range(1, 15):
            # 价格波动，偶尔创历史新低
            price = base + random.uniform(-30, 10)
            base = min(base, price)  # 让价格有下降趋势
            product_price_data.append((pid, f"2024-04-{day:02d}", round(price, 2)))

    conn.executemany("INSERT INTO product_price (id, ds, price) VALUES (?, ?, ?)", product_price_data)

    print(f"     user_visits: {len(user_visits_data)} rows")
    print(f"     live_log: {len(live_log_data)} rows")
    print(f"     user_spend: {len(user_spend_data)} rows")
    print(f"     orders: {len(orders_data)} rows")
    print(f"     product_price: {len(product_price_data)} rows")
