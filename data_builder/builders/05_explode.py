"""Builder for Category 05: 炸裂函数"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== raw_intervals 表：区间合并 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_intervals (
            start INTEGER,
            "end" INTEGER
        )
    """)

    random.seed(500)
    intervals_data = []
    # 手动构造一组有重叠的区间，确保合并后有结果
    raw_pairs = [
        (1, 5),
        (3, 8),
        (10, 12),
        (11, 15),
        (20, 25),
        (22, 28),
        (30, 35),
        (40, 45),
        (50, 55),
        (52, 60),
        (62, 68),
        (65, 70),
    ]
    for start, end in raw_pairs:
        intervals_data.append((start, end))

    conn.executemany('INSERT INTO raw_intervals (start, "end") VALUES (?, ?)', intervals_data)

    print(f"     raw_intervals: {len(intervals_data)} rows")
