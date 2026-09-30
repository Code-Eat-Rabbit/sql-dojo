"""Builder for Category 09: 合并区间"""

import random


def build(conn):
    cur = conn.cursor()
    # ===== status_log 表：状态标记 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS status_log (
            id INTEGER,
            status VARCHAR(128),
            start_time VARCHAR(20)
        )
    """)

    random.seed(900)
    status_log_data = []
    statuses = ["在线", "忙碌", "离线", "在线", "离开"]
    for obj_id in range(1, 4):
        hour = 8
        for i, status in enumerate(statuses):
            start = f"2024-05-{10+obj_id:02d} {hour:02d}:00:00"
            status_log_data.append((obj_id, status, start))
            hour += random.randint(1, 4)

    cur.executemany("INSERT INTO status_log (id, status, start_time) VALUES (%s, %s, %s)", status_log_data)

    # ===== data_table 表：填补缺失值（含 NULL） =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS data_table (
            id INTEGER,
            date VARCHAR(10),
            value DOUBLE
        )
    """)

    data_table_data = []
    for group_id in range(1, 4):
        val = random.uniform(10, 100)
        for day in range(1, 11):
            if random.random() < 0.3:
                # 约 30% 的行为 NULL
                data_table_data.append((group_id, f"2024-06-{day:02d}", None))
            else:
                val += random.uniform(-5, 5)
                data_table_data.append((group_id, f"2024-06-{day:02d}", round(val, 2)))

    cur.executemany("INSERT INTO data_table (id, date, value) VALUES (%s, %s, %s)", data_table_data)

    print(f"     status_log: {len(status_log_data)} rows")
    print(f"     data_table: {len(data_table_data)} rows")
