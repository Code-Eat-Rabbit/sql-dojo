"""只读 SQL 执行器：白名单校验 + 只读会话 + 超时 + 行数上限"""

import datetime as _dt
import time
from decimal import Decimal

import pymysql.cursors

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


def _translate_error(e: pymysql.err.Error) -> MysqlExecutionError:
    code = e.args[0] if e.args else 0
    detail = str(e.args[1]) if len(e.args) > 1 else str(e)
    if code == 1792:  # ER_CANT_EXECUTE_IN_READ_ONLY_TRANSACTION
        msg = "只允许查询语句：当前会话为只读（READ ONLY）"
    elif code == 1064:  # ER_PARSE_ERROR
        msg = f"SQL 语法错误：{detail}"
    elif code == 3024:  # ER_QUERY_TIMEOUT
        msg = "执行超时（受 max_execution_time 限制），请优化查询"
    elif code == 1146:  # ER_NO_SUCH_TABLE
        msg = f"表不存在：{detail}"
    else:
        msg = detail
    return MysqlExecutionError(code, msg)


def execute_statements(schema: str, stmts: list[str],
                       timeout_ms: int = DEFAULT_TIMEOUT_MS) -> list[dict]:
    """在只读会话中依次执行语句，返回全部结果集（原始值，判题用）。

    每个结果集：{"columns": list[str], "rows": list[tuple], "truncated": bool}
    行数上限 MAX_ROWS=500，两侧（用户/参考）同一上限保证判题公平。
    """
    try:
        conn = get_practice_connection(schema)
    except pymysql.err.OperationalError as e:
        raise MysqlUnavailableError() from e
    try:
        cur = conn.cursor(pymysql.cursors.Cursor)  # 数组行（非 Dict）
        cur.execute("SET SESSION TRANSACTION READ ONLY")
        cur.execute(f"SET SESSION max_execution_time = {int(timeout_ms)}")
        results = []
        for stmt in stmts:
            try:
                cur.execute(stmt)
            except pymysql.err.Error as e:
                raise _translate_error(e) from e
            if cur.description:
                rows = cur.fetchmany(MAX_ROWS + 1)
                results.append({
                    "columns": [d[0] for d in cur.description],
                    "rows": rows[:MAX_ROWS],
                    "truncated": len(rows) > MAX_ROWS,
                })
        return results
    finally:
        conn.close()


def _json_safe(v):
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", "replace")
    if isinstance(v, (Decimal, _dt.datetime, _dt.date, _dt.timedelta, _dt.time)):
        return str(v)
    return v


def run_readonly(schema: str, sql: str,
                 timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    """校验 + 执行，返回最后一个结果集（JSON 安全，API 展示用）"""
    stmts = assert_executable(sql)
    t0 = time.perf_counter()
    results = execute_statements(schema, stmts, timeout_ms=timeout_ms)
    elapsed = int((time.perf_counter() - t0) * 1000)
    if not results:
        return {"columns": [], "rows": [], "rowCount": 0,
                "truncated": False, "elapsedMs": elapsed}
    last = results[-1]
    return {
        "columns": last["columns"],
        "rows": [[_json_safe(v) for v in row] for row in last["rows"]],
        "rowCount": len(last["rows"]),
        "truncated": last["truncated"],
        "elapsedMs": elapsed,
    }
