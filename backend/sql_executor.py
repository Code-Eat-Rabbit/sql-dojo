"""只读 SQL 执行器：白名单校验 + 只读会话 + 超时 + 行数上限"""

import time

import pymysql

from backend.database import get_practice_connection

MAX_SQL_BYTES = 64 * 1024
MAX_ROWS = 500
DEFAULT_TIMEOUT_MS = 5000
READONLY_VERBS = {"SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"}


class SqlRejectedError(Exception):
    """请求被白名单/大小/空语句拒绝（HTTP 400）"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class MysqlUnavailableError(Exception):
    """MySQL 不可连接（HTTP 503）"""

    def __init__(self, message: str = "MySQL 未启动，请先运行 bash start.sh"):
        self.message = message
        super().__init__(message)


class MysqlExecutionError(Exception):
    """MySQL 执行报错（HTTP 400），message 已转译为友好中文"""

    def __init__(self, mysql_code: int, message: str):
        self.mysql_code = mysql_code
        self.message = message
        super().__init__(message)


def strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        cut = line.find("--")
        lines.append(line if cut == -1 else line[:cut])
    return "\n".join(lines)


def split_statements(sql: str) -> list[str]:
    return [s.strip() for s in strip_comments(sql).split(";") if s.strip()]


def _first_verb(stmt: str) -> str:
    return stmt.split(None, 1)[0].upper()


def assert_executable(sql: str) -> list[str]:
    """大小校验 + 白名单校验，返回语句列表；不合规抛 SqlRejectedError"""
    if len(sql.encode("utf-8")) > MAX_SQL_BYTES:
        raise SqlRejectedError(
            "sql_too_large", f"SQL 超过 {MAX_SQL_BYTES // 1024}KB 上限")
    stmts = split_statements(sql)
    if not stmts:
        raise SqlRejectedError("empty_sql", "没有可执行的 SQL 语句")
    for s in stmts:
        if _first_verb(s) not in READONLY_VERBS:
            raise SqlRejectedError(
                "forbidden_statement",
                f"只允许查询语句（SELECT/WITH/SHOW/DESC/EXPLAIN），"
                f"已拒绝：{_first_verb(s)}",
            )
    return stmts


def is_gradable_sql(sql: str) -> bool:
    """参考答案是否全为查询语句（seed 时用于 gradable 标记）"""
    stmts = split_statements(sql)
    return bool(stmts) and all(_first_verb(s) in READONLY_VERBS for s in stmts)
