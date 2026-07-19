"""数据库管理：progress.db + 多库连接 + manifest 加载"""

import re
import sqlite3
import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES_DIR = BASE_DIR / "databases"
PROGRESS_DB = DATABASES_DIR / "progress.db"


def init_progress_db():
    """创建 progress.db 及 problems/progress 表"""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(PROGRESS_DB)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS problems (
                id TEXT PRIMARY KEY,
                category_id TEXT NOT NULL,
                title TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                db_path TEXT NOT NULL,
                table_names TEXT DEFAULT '[]',
                description TEXT DEFAULT '',
                reference_sql TEXT DEFAULT '',
                hints TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS progress (
                problem_id TEXT PRIMARY KEY REFERENCES problems(id),
                status TEXT DEFAULT 'not_started',
                completed_count INTEGER DEFAULT 0,
                mastery_level INTEGER DEFAULT 0,
                last_practiced_at TIMESTAMP,
                notes TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def seed_problems():
    """将 manifest.py 中的题目数据同步到 progress.db 的 problems 表"""
    import sys
    original_path = sys.path.copy()
    sys.path.insert(0, str(BASE_DIR / "data_builder"))
    try:
        from manifest import CATEGORIES
    finally:
        sys.path = original_path

    with sqlite3.connect(str(PROGRESS_DB)) as conn:
        for cat in CATEGORIES:
            for prob in cat.problems:
                conn.execute("""
                    INSERT OR REPLACE INTO problems
                        (id, category_id, title, difficulty, db_path, table_names,
                         description, reference_sql, hints, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prob.id, prob.category_id, prob.title, prob.difficulty,
                    str(DATABASES_DIR / cat.db_file),
                    json.dumps(prob.tables, ensure_ascii=False),
                    prob.description.strip(),
                    prob.reference_sql.strip(),
                    json.dumps(prob.hints, ensure_ascii=False),
                    json.dumps(prob.tags, ensure_ascii=False),
                ))
                # Ensure progress row exists
                conn.execute("""
                    INSERT OR IGNORE INTO progress (problem_id)
                    VALUES (?)
                """, (prob.id,))


def get_progress_connection() -> sqlite3.Connection:
    """获取 progress.db 连接"""
    conn = sqlite3.connect(str(PROGRESS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_practice_db_path(db_file: str) -> Path:
    """获取练习数据库的绝对路径"""
    resolved = (DATABASES_DIR / db_file).resolve()
    # Verify the resolved path is under DATABASES_DIR (prevent path traversal)
    if not str(resolved).startswith(str(DATABASES_DIR.resolve()) + "/"):
        raise ValueError(f"Path traversal detected: {db_file}")
    return resolved


def get_table_schema(db_file: str, table_name: str) -> dict:
    """读取指定表的结构和前 5 行数据"""
    # Validate table_name to prevent SQL injection
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        return {}

    db_path = DATABASES_DIR / db_file
    if not db_path.exists():
        return {}

    try:
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row

            # 列信息
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            # 行数
            row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            # 前 5 行
            rows = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
    except sqlite3.OperationalError:
        return {}

    return {
        "name": table_name,
        "columns": [{"name": c["name"], "type": c["type"]} for c in columns],
        "row_count": row_count,
        "sample_rows": [dict(r) for r in rows],
    }


if __name__ == "__main__":
    init_progress_db()
    seed_problems()
    print(f"Progress DB initialized at {PROGRESS_DB}")
