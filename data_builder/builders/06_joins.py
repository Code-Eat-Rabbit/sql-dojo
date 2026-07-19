"""Builder for Category 06: 关联应用"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== student 表 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY,
            student_name TEXT
        )
    """)

    random.seed(600)
    names = ["张三", "李四", "王五", "赵六", "钱七"]
    student_data = [(i + 1, name) for i, name in enumerate(names)]
    conn.executemany("INSERT INTO student (id, student_name) VALUES (?, ?)", student_data)

    # ===== class 表 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS class (
            id INTEGER PRIMARY KEY,
            class_name TEXT
        )
    """)

    class_data = [(1, "语文"), (2, "数学"), (3, "英语"), (4, "物理")]
    conn.executemany("INSERT INTO class (id, class_name) VALUES (?, ?)", class_data)

    # ===== sc 表：成绩 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sc (
            sid INTEGER,
            cid INTEGER,
            score REAL
        )
    """)

    sc_data = []
    for sid in range(1, 6):
        for cid in range(1, 5):
            score = random.randint(40, 100)
            sc_data.append((sid, cid, float(score)))

    # 确保至少有一个学生所有科目 > 60
    # 学生5（钱七）所有科目都设为 > 60
    sc_data_with_good = []
    for sid in range(1, 5):
        for cid in range(1, 5):
            score = random.randint(40, 100)
            sc_data_with_good.append((sid, cid, float(score)))
    for cid in range(1, 5):
        sc_data_with_good.append((5, cid, float(random.randint(65, 95))))

    conn.executemany("INSERT INTO sc (sid, cid, score) VALUES (?, ?, ?)", sc_data_with_good)

    # ===== fans 表：关注关系 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fans (
            from_user TEXT,
            to_user TEXT
        )
    """)

    fans_data = [
        ("alice", "bob"),
        ("bob", "alice"),
        ("alice", "charlie"),
        ("charlie", "alice"),
        ("bob", "dave"),
        ("dave", "bob"),
        ("charlie", "eve"),
        ("eve", "frank"),
        ("alice", "dave"),
        ("frank", "alice"),
        ("eve", "charlie"),
        ("bob", "charlie"),
    ]
    conn.executemany("INSERT INTO fans (from_user, to_user) VALUES (?, ?)", fans_data)

    print(f"     student: {len(student_data)} rows")
    print(f"     class: {len(class_data)} rows")
    print(f"     sc: {len(sc_data_with_good)} rows")
    print(f"     fans: {len(fans_data)} rows")
