"""Builder for Category 01: 连续登陆"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    """创建表并插入练习数据"""
    # ===== test 表：用户登录记录 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER,
            date TEXT
        )
    """)

    # 生成数据：5 个用户，每人登录 8-15 天
    random.seed(42)
    test_data = []
    for user_id in range(1, 6):
        days = []
        start_day = random.randint(1, 20)
        for i in range(random.randint(8, 15)):
            day = start_day + i
            # 随机跳过 1-3 天来制造间断
            if random.random() < 0.2:
                start_day += random.randint(2, 4)
                day = start_day + i
            days.append(f"2024-01-{day:02d}")
        # 添加一些重复日期（同一天多次登录）
        if random.random() < 0.3:
            days.insert(random.randint(0, len(days)), random.choice(days))
        for d in days:
            test_data.append((user_id, d))

    conn.executemany("INSERT INTO test (id, date) VALUES (?, ?)", test_data)

    # ===== account 表：账户余额（拓展1） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account (
            user_id INTEGER,
            date TEXT,
            balance REAL
        )
    """)

    account_data = []
    for user_id in range(1, 4):
        bal = 800.0
        for day in range(1, 21):
            # 随机波动
            bal += random.uniform(-100, 150)
            bal = max(0, bal)
            account_data.append((user_id, f"2024-02-{day:02d}", round(bal, 2)))
    conn.executemany(
        "INSERT INTO account (user_id, date, balance) VALUES (?, ?, ?)",
        account_data
    )

    # ===== test_xiaoming 表：日期区间（拓展2） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_xiaoming (
            id INTEGER,
            name TEXT,
            start_date TEXT,
            end_date TEXT
        )
    """)

    xm_data = [
        (1, "小明", "2024-01-01", "2024-01-05"),
        (1, "小明", "2024-01-06", "2024-01-10"),
        (1, "小明", "2024-01-15", "2024-01-20"),
        (2, "小红", "2024-02-01", "2024-02-03"),
        (2, "小红", "2024-02-03", "2024-02-07"),
        (2, "小红", "2024-02-10", "2024-02-12"),
    ]
    conn.executemany(
        "INSERT INTO test_xiaoming (id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
        xm_data
    )

    # ===== games 表：胜负记录（拓展3） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            user_id INTEGER,
            date TEXT,
            result TEXT
        )
    """)

    game_data = []
    for user_id in range(1, 4):
        for day in range(1, 16):
            result = random.choice(["win", "win", "win", "lose"])  # 75% 胜率
            game_data.append((user_id, f"2024-03-{day:02d}", result))
    conn.executemany(
        "INSERT INTO games (user_id, date, result) VALUES (?, ?, ?)",
        game_data
    )

    print(f"     test: {len(test_data)} rows")
    print(f"     account: {len(account_data)} rows")
    print(f"     test_xiaoming: {len(xm_data)} rows")
    print(f"     games: {len(game_data)} rows")
