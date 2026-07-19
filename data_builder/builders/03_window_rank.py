"""Builder for Category 03: 三种排序开窗"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== scores 表：演示三种排序 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            student TEXT,
            score INTEGER
        )
    """)

    random.seed(300)
    students = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]
    scores_data = []
    # 制造并列分数，展示 rank 和 dense_rank 的区别
    score_pool = [95, 95, 88, 88, 88, 82, 78, 72, 72, 65, 60, 55]
    for i, student in enumerate(students):
        s = score_pool[i % len(score_pool)]
        scores_data.append((student, s))

    conn.executemany("INSERT INTO scores (student, score) VALUES (?, ?)", scores_data)

    # ===== student_scores 表：每学生第二高科目 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student_scores (
            student TEXT,
            subject TEXT,
            score INTEGER
        )
    """)

    subjects = ["语文", "数学", "英语", "物理", "化学"]
    student_scores_data = []
    for student in students[:5]:
        for subject in subjects:
            score = random.randint(50, 100)
            # 制造一些并列第二的情况
            student_scores_data.append((student, subject, score))

    conn.executemany("INSERT INTO student_scores (student, subject, score) VALUES (?, ?, ?)", student_scores_data)

    print(f"     scores: {len(scores_data)} rows")
    print(f"     student_scores: {len(student_scores_data)} rows")
