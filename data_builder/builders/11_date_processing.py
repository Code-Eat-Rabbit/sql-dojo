"""Builder for Category 11: 日期处理"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== date_table 表：各种日期格式 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS date_table (
            date TEXT
        )
    """)

    random.seed(1100)
    date_data = []
    # 覆盖各个月份和年份，用于测试 year / quarter / half / mm 等格式
    import datetime
    start = datetime.date(2023, 1, 1)
    for i in range(40):
        d = start + datetime.timedelta(days=random.randint(10, 60) + i * 7)
        if d.year <= 2025:
            date_data.append((d.strftime("%Y-%m-%d"),))

    # 确保有重复月份用于测试
    date_data = list(set(date_data))
    conn.executemany("INSERT INTO date_table (date) VALUES (?)", date_data)

    print(f"     date_table: {len(date_data)} rows")
