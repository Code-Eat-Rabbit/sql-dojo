"""Builder for Category 08: 数据展开与收缩"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== user_tags 表：逗号分隔标签（展开用） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tags (
            user_id INTEGER,
            tags TEXT
        )
    """)

    random.seed(800)
    user_tags_data = [
        (1, "技术,后端,Python"),
        (2, "技术,前端,React,TypeScript"),
        (3, "产品,增长,数据分析"),
        (4, "设计,UI,UX"),
        (5, "运营,内容,社区"),
        (6, "技术,DevOps,K8s,Docker"),
        (7, "产品,中台,B端"),
        (8, "技术,算法,机器学习,NLP"),
    ]
    conn.executemany("INSERT INTO user_tags (user_id, tags) VALUES (?, ?)", user_tags_data)

    # ===== user_tag_rows 表：已展开的行格式（收缩用） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tag_rows (
            user_id INTEGER,
            tag TEXT
        )
    """)

    user_tag_rows_data = []
    for uid, tags_str in user_tags_data:
        for tag in tags_str.split(","):
            user_tag_rows_data.append((uid, tag))

    conn.executemany("INSERT INTO user_tag_rows (user_id, tag) VALUES (?, ?)", user_tag_rows_data)

    print(f"     user_tags: {len(user_tags_data)} rows")
    print(f"     user_tag_rows: {len(user_tag_rows_data)} rows")
