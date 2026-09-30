"""参考答案冒烟测试：逐题在 MySQL 上执行 reference_sql。

用法：uv run python data_builder/smoke_test.py
分类：
  executable   逐语句执行，必须 0 报错
  ddl          答案全为 CREATE TABLE，在 smoke_scratch 库执行后清理
  comment_only 纯注释说明题，跳过
  stub         -- 待补充，跳过
另外对 executable 答案做方言 lint（|| / JSON_EACH / mydb. 等禁止模式）。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_builder import db as mysql_db
from data_builder.manifest import CATEGORIES, get_all_problems

SCHEMAS = {cat.id: cat.db_file[:-3] for cat in CATEGORIES}

FORBIDDEN_PATTERNS = [
    (r"\|\|", "SQLite 拼接 || → 用 CONCAT()"),
    (r"JSON_EACH", "SQLite JSON_EACH → 用 JSON_TABLE()"),
    (r"julianday|strftime|sqlite_master|AUTOINCREMENT", "SQLite 专属语法"),
    (r"\bmydb\.", "跨库前缀 mydb. → 去掉，题内表就在当前 schema"),
    (r"GROUP_CONCAT\((?![^)]*SEPARATOR)[^)]*,\s*'", "GROUP_CONCAT 双参分隔符 → 用 SEPARATOR"),
]


def strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        cut = line.find("--")
        lines.append(line if cut == -1 else line[:cut])
    return "\n".join(lines)


def statements(sql: str) -> list[str]:
    return [s.strip() for s in strip_comments(sql).split(";") if s.strip()]


def classify(sql: str) -> str:
    if "待补充" in sql:
        return "stub"
    stmts = statements(sql)
    if not stmts:
        return "comment_only"
    if all(s.lstrip().upper().startswith("CREATE") for s in stmts):
        return "ddl"
    return "executable"


def lint(sql: str) -> list[str]:
    return [msg for pat, msg in FORBIDDEN_PATTERNS if re.search(pat, sql, re.IGNORECASE)]


def run_problem(prob) -> tuple[str, str]:
    kind = classify(prob.reference_sql)
    if kind in ("stub", "comment_only"):
        return kind, "skip"
    target = mysql_db.reset_schema("smoke_scratch") if kind == "ddl" \
        else mysql_db.connect(SCHEMAS[prob.category_id])
    try:
        issues = lint(prob.reference_sql)
        if issues:
            return kind, "lint: " + "; ".join(issues)
        for stmt in statements(prob.reference_sql):
            with target.cursor() as cur:
                cur.execute(stmt)
                if cur.description:
                    cur.fetchall()
        return kind, "ok"
    finally:
        target.close()


def main() -> int:
    mysql_db.wait_for_mysql()
    failures = []
    counts = {"executable": 0, "ddl": 0, "comment_only": 0, "stub": 0}
    for prob in get_all_problems():
        try:
            kind, status = run_problem(prob)
        except Exception as e:  # pymysql 报错等
            kind = classify(prob.reference_sql)
            status = f"FAIL: {str(e)[:160]}"
        counts[kind] = counts.get(kind, 0) + 1
        mark = "✓" if status == "ok" or status == "skip" else "✗"
        print(f"[{mark}] {prob.id:<6} {kind:<12} {status}")
        if mark == "✗":
            failures.append(prob.id)
    # 清理 scratch 库
    conn = mysql_db.connect()
    with conn.cursor() as cur:
        cur.execute("DROP DATABASE IF EXISTS smoke_scratch")
    conn.close()
    print(f"\n统计: {counts}")
    print("失败:", failures if failures else "无")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
