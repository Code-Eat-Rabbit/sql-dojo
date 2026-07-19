"""Builder for Category 07: 留存计算"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== user_active 表：用户活跃记录 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_active (
            user_id INTEGER,
            date TEXT
        )
    """)

    random.seed(700)
    user_active_data = []
    for user_id in range(1, 21):
        # 首次活跃日期（Day 0）
        first_day = random.randint(1, 15)
        user_active_data.append((user_id, f"2024-01-{first_day:02d}"))

        # 后续活跃日期（随机间隔，有些在 Day 7 活跃）
        current_day = first_day
        for _ in range(random.randint(1, 8)):
            gap = random.randint(1, 5)
            current_day += gap
            if current_day <= 31:
                user_active_data.append((user_id, f"2024-01-{current_day:02d}"))

        # 确保部分用户在 Day7 活跃（约 40% 的用户）
        day7 = first_day + 7
        if day7 <= 31 and random.random() < 0.4:
            user_active_data.append((user_id, f"2024-01-{day7:02d}"))

    conn.executemany("INSERT INTO user_active (user_id, date) VALUES (?, ?)", user_active_data)

    print(f"     user_active: {len(user_active_data)} rows")
