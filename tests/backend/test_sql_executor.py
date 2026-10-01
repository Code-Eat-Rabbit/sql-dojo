"""sql_executor 纯单元：拆句、白名单、大小限制（不连 MySQL）"""

import pytest

from backend.sql_executor import (
    SqlRejectedError,
    assert_executable,
    is_gradable_sql,
    split_statements,
)


def test_split_statements_strips_comments_and_blanks():
    sql = "-- 查询\nSELECT 1;\n\nSELECT 2; -- tail\n"
    assert split_statements(sql) == ["SELECT 1", "SELECT 2"]


def test_assert_executable_accepts_readonly_verbs():
    for s in [
        "SELECT 1",
        "with t as (select 1) select * from t",  # 小写也接受
        "SHOW TABLES",
        "DESC scores",
        "DESCRIBE scores",
        "EXPLAIN SELECT 1",
    ]:
        assert assert_executable(s)  # 不抛错即通过


def test_assert_executable_rejects_writes():
    for s in [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET a = 1",
        "DELETE FROM t",
        "CREATE TABLE x (id INT)",
        "DROP TABLE t",
        "TRUNCATE TABLE t",
    ]:
        with pytest.raises(SqlRejectedError) as ei:
            assert_executable(s)
        assert ei.value.code == "forbidden_statement"


def test_assert_executable_rejects_write_in_later_statement():
    with pytest.raises(SqlRejectedError):
        assert_executable("SELECT 1; DELETE FROM t")


def test_assert_executable_rejects_empty_and_oversize():
    with pytest.raises(SqlRejectedError) as ei:
        assert_executable("-- 只有注释")
    assert ei.value.code == "empty_sql"

    with pytest.raises(SqlRejectedError) as ei:
        assert_executable("SELECT '" + "x" * (64 * 1024) + "'")
    assert ei.value.code == "sql_too_large"


def test_is_gradable_sql():
    assert is_gradable_sql("SELECT 1 FROM t;") is True
    assert is_gradable_sql("WITH x AS (SELECT 1) SELECT * FROM x") is True
    assert is_gradable_sql("CREATE TABLE a (id INT);") is False
    assert is_gradable_sql("-- 说明题\n没有可执行语句") is False
