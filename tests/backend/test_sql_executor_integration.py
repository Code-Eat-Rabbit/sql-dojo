"""sql_executor 集成：连接真实 MySQL 容器执行"""

import pytest

from backend.database import schema_exists
from backend.sql_executor import (
    MysqlExecutionError,
    MysqlUnavailableError,
    execute_statements,
    run_readonly,
)

pytestmark = pytest.mark.skipif(
    not schema_exists("01_continuous_login"),
    reason="MySQL 容器未运行（先 bash start.sh）",
)


def test_run_readonly_select():
    r = run_readonly("01_continuous_login", "SELECT id FROM test LIMIT 3")
    assert r["columns"] == ["id"]
    assert r["rowCount"] == 3
    assert len(r["rows"]) == 3
    assert r["truncated"] is False
    assert r["elapsedMs"] >= 0


def test_multi_statement_returns_last_result_set():
    r = run_readonly("01_continuous_login", "SELECT 1 AS a; SELECT 2 AS b;")
    assert r["columns"] == ["b"]
    assert r["rows"] == [[2]]


def test_row_cap_marks_truncated():
    parts = ["SELECT 1 AS n"] + [f"SELECT {i}" for i in range(2, 602)]  # 601 行
    r = run_readonly("01_continuous_login", " UNION ALL ".join(parts))
    assert r["rowCount"] == 500
    assert r["truncated"] is True


def test_write_bypassing_whitelist_rejected_by_readonly():
    # WITH 通过白名单，但 READ ONLY 会话拒绝写操作（MySQL 错误 1792）
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly(
            "01_continuous_login",
            "WITH t AS (SELECT 1 AS x) UPDATE test SET id = id",
        )
    assert ei.value.mysql_code == 1792
    assert "只允许查询语句" in ei.value.message


def test_syntax_error_translated():
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly("01_continuous_login", "SELECT FROM WHERE")
    assert ei.value.mysql_code == 1064
    assert "语法错误" in ei.value.message


def test_timeout_raises():
    # 4 维自交叉积 + 非等值谓词必然超过 1s，触发 max_execution_time（错误 3024）
    # 注：MySQL 8.4 优化器会把裸 COUNT(*) 笛卡尔积常量折叠，必须加谓词强制逐行求值
    sql = ("SELECT COUNT(*) FROM attendance a, attendance b, "
           "attendance c, attendance d WHERE a.check_in > b.check_in")
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly("10_hr_warehouse", sql, timeout_ms=1000)
    assert ei.value.mysql_code == 3024


def test_mysql_unavailable(monkeypatch):
    import backend.database as db

    monkeypatch.setattr(db, "MYSQL_PORT", 59999)
    with pytest.raises(MysqlUnavailableError):
        run_readonly("01_continuous_login", "SELECT 1")


def test_execute_statements_keeps_raw_values():
    # 判题用原始值（不经 JSON 转换），execute_statements 直接暴露
    sets = execute_statements("03_window_rank", ["SELECT score FROM scores LIMIT 1"])
    assert sets[0]["columns"] == ["score"]
    assert len(sets[0]["rows"]) == 1
    from decimal import Decimal
    assert isinstance(sets[0]["rows"][0][0], (int, float, Decimal))  # 原生数值
