"""Builder for Category 14: 趣味 SQL

Only creates tables for non-stub problems:
  - 14_01 接雨水: heights
  - 14_03 赛马: race_result
Skips stubs: 14_02, 14_04
"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== heights 表：接雨水问题 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS heights (
            height INTEGER
        )
    """)

    random.seed(1400)
    # 经典的接雨水柱子高度，确保能接到水
    heights_vals = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    heights_data = [(h,) for h in heights_vals]

    conn.executemany("INSERT INTO heights (height) VALUES (?)", heights_data)

    # ===== race_result 表：赛马问题 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS race_result (
            horse TEXT,
            time REAL
        )
    """)

    horses = ["赤兔", "的卢", "绝影", "爪黄飞电", "乌云踏雪", "照夜玉狮子", "快航", "惊帆"]
    times = []
    base = random.uniform(55, 65)
    for _ in horses:
        base += random.uniform(0.3, 1.5)
        times.append(round(base, 2))

    # shuffle to mix up ordering
    random.shuffle(horses)
    race_data = list(zip(horses, times))

    conn.executemany("INSERT INTO race_result (horse, time) VALUES (?, ?)", race_data)

    print(f"     heights: {len(heights_data)} rows")
    print(f"     race_result: {len(race_data)} rows")
