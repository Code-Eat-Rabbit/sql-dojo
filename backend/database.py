"""数据库管理：progress.db + 多库连接 + manifest 加载"""

import re
import sqlite3
import json
from pathlib import Path
from typing import Optional

import pymysql
import pymysql.cursors

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "practice"


def get_practice_connection(schema: str | None = None) -> pymysql.connections.Connection:
    """获取练习库 MySQL 连接（DictCursor，便于直接输出 JSON）"""
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=schema,
        charset="utf8mb4", autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_schema_name(db_file: str) -> str:
    """manifest 的 db_file（如 01_continuous_login.db）→ MySQL schema 名"""
    schema = db_file[:-3] if db_file.endswith(".db") else db_file
    if not re.match(r"^[0-9a-z_]+$", schema):
        raise ValueError(f"Invalid schema name: {db_file}")
    return schema


def schema_exists(schema: str) -> bool:
    """检查练习 schema 是否已生成（容器未启动时返回 False 而不是抛错）"""
    try:
        conn = get_practice_connection()
    except pymysql.err.OperationalError:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (schema,),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def mysql_cli_command(schema: str) -> str:
    return f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u{MYSQL_USER} -p{MYSQL_PASSWORD} {schema}"


def mysql_jdbc_url(schema: str) -> str:
    return f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{schema}"


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
                    cat.db_file[:-3],  # MySQL schema 名（列名沿用 db_path，避免迁移 progress.db）
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


def get_table_schema(schema: str, table_name: str) -> dict:
    """读取指定 schema 中表的结构和前 5 行数据（MySQL）"""
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        return {}

    try:
        conn = get_practice_connection(schema)
    except pymysql.err.OperationalError:
        return {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name AS `column_name`, data_type AS `data_type` "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s ORDER BY `ordinal_position`",
                (schema, table_name),
            )
            columns = cur.fetchall()
            if not columns:
                return {}
            cur.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
            row_count = cur.fetchone()["cnt"]
            cur.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
            rows = cur.fetchall()
    except pymysql.err.Error:
        return {}
    finally:
        conn.close()

    return {
        "name": table_name,
        "columns": [{"name": c["column_name"], "type": c["data_type"]} for c in columns],
        "row_count": row_count,
        "sample_rows": rows,
    }


if __name__ == "__main__":
    init_progress_db()
    seed_problems()
    print(f"Progress DB initialized at {PROGRESS_DB}")
