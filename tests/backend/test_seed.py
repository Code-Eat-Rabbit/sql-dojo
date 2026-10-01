"""seed 迁移：gradable/ordered 列 + drafts 表"""

import sqlite3


def test_seed_marks_gradable(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    rows = dict(conn.execute("SELECT id, gradable FROM problems").fetchall())
    conn.close()
    assert rows["01_01"] == 1   # 查询题可判题
    assert rows["01_04"] == 0   # 总结题（纯注释）不可判题
    assert rows["10_01"] == 0   # 说明题不可判题
    assert rows["10_02"] == 0   # DDL 建表题不可判题


def test_ordered_column_defaults_zero(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    val = conn.execute(
        "SELECT ordered FROM problems WHERE id = '01_01'").fetchone()[0]
    conn.close()
    assert val == 0


def test_drafts_table_created(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    conn.execute(
        "INSERT INTO drafts (problem_id, sql_text, updated_at) "
        "VALUES ('01_01', 'SELECT 1', '2026-10-01')")
    conn.commit()
    val = conn.execute(
        "SELECT sql_text FROM drafts WHERE problem_id = '01_01'").fetchone()[0]
    conn.close()
    assert val == "SELECT 1"
