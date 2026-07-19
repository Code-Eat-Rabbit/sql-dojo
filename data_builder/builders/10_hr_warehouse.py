"""Builder for Category 10: 人事数仓表格设计"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    # ===== employee 表 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employee (
            emp_id INTEGER PRIMARY KEY,
            name TEXT,
            dept_id INTEGER,
            hire_date TEXT,
            status TEXT
        )
    """)

    random.seed(1000)
    depts = {1: "技术部", 2: "产品部", 3: "设计部", 4: "运营部"}
    last_names = ["张", "李", "王", "赵", "陈", "刘", "黄", "周", "吴", "郑"]
    first_names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "勇", "艳"]

    employee_data = []
    for emp_id in range(1, 21):
        name = random.choice(last_names) + random.choice(first_names)
        dept_id = random.choice(list(depts.keys()))
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hire_date = f"201{random.randint(8,9)}-{month:02d}-{day:02d}"
        status = random.choice(["在职", "在职", "在职", "离职"])  # 75% 在职
        employee_data.append((emp_id, name, dept_id, hire_date, status))

    conn.executemany(
        "INSERT INTO employee (emp_id, name, dept_id, hire_date, status) VALUES (?, ?, ?, ?, ?)",
        employee_data
    )

    # ===== salary 表 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS salary (
            emp_id INTEGER,
            month TEXT,
            base_salary REAL,
            bonus REAL,
            PRIMARY KEY (emp_id, month)
        )
    """)

    salary_data = []
    for emp_id in range(1, 13):  # 只给 12 个员工发薪
        base = round(random.uniform(5000, 25000), 2)
        for m in range(1, 10):
            month_str = f"2024-{m:02d}"
            bonus = round(random.uniform(0, 5000), 2)
            salary_data.append((emp_id, month_str, base, bonus))

    conn.executemany(
        "INSERT INTO salary (emp_id, month, base_salary, bonus) VALUES (?, ?, ?, ?)",
        salary_data
    )

    # ===== attendance 表 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            emp_id INTEGER,
            date TEXT,
            check_in TEXT,
            check_out TEXT
        )
    """)

    attendance_data = []
    for emp_id in range(1, 16):
        for day in range(1, 22):
            if random.random() < 0.85:  # 85% 出勤率
                in_hour = random.randint(7, 9)
                in_min = random.randint(0, 59)
                check_in = f"{in_hour:02d}:{in_min:02d}:00"
                out_hour = random.randint(17, 21)
                out_min = random.randint(0, 59)
                check_out = f"{out_hour:02d}:{out_min:02d}:00"
                attendance_data.append((emp_id, f"2024-07-{day:02d}", check_in, check_out))

    conn.executemany(
        "INSERT INTO attendance (emp_id, date, check_in, check_out) VALUES (?, ?, ?, ?)",
        attendance_data
    )

    print(f"     employee: {len(employee_data)} rows")
    print(f"     salary: {len(salary_data)} rows")
    print(f"     attendance: {len(attendance_data)} rows")
