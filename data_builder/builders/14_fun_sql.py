"""Builder for Category 14: 趣味 SQL

Only creates tables for non-stub problems:
  - 14_01 接雨水: heights
  - 14_03 赛马: race_result
Skips stubs: 14_02, 14_04
"""

import random


def build(conn):
    cur = conn.cursor()
    # ===== heights 表：接雨水问题（idx 列提供确定的柱子顺序） =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS heights (
            idx INTEGER,
            height INTEGER
        )
    """)

    random.seed(1400)
    # 经典的接雨水柱子高度，确保能接到水
    heights_vals = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    heights_data = [(i + 1, h) for i, h in enumerate(heights_vals)]

    cur.executemany("INSERT INTO heights (idx, height) VALUES (%s, %s)", heights_data)

    # ===== race_result 表：赛马问题 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS race_result (
            horse VARCHAR(128),
            time DOUBLE
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

    cur.executemany("INSERT INTO race_result (horse, time) VALUES (%s, %s)", race_data)

    print(f"     heights: {len(heights_data)} rows")
    print(f"     race_result: {len(race_data)} rows")
