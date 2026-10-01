"""Builder for Category 13: JSON 解析"""

import json
import random


def build(conn):
    cur = conn.cursor()
    # ===== user_profiles 表：含 JSON 字段 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER,
            data TEXT
        )
    """)

    random.seed(1300)
    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    cities = ["Beijing", "Shanghai", "Shenzhen", "Hangzhou", "Chengdu"]
    hobbies_pool = ["reading", "swimming", "coding", "hiking", "gaming", "cooking"]

    json_data = []
    for i, name in enumerate(names):
        obj = {
            "name": name,
            "age": random.randint(22, 45),
            "city": random.choice(cities),
            "items": random.sample(hobbies_pool, random.randint(2, 4))
        }
        json_data.append((i + 1, json.dumps(obj, ensure_ascii=False)))

    cur.executemany("INSERT INTO user_profiles (id, data) VALUES (%s, %s)", json_data)

    print(f"     user_profiles: {len(json_data)} rows")
