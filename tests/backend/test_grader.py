"""grader：值归一化与结果集比对"""

import datetime as dt
from decimal import Decimal

from backend.grader import grade, normalize_value


def set_(cols, rows):
    return {"columns": list(cols), "rows": [tuple(r) for r in rows],
            "truncated": False}


def test_normalize_numeric_equivalence():
    assert normalize_value(1) == normalize_value(Decimal("1.0"))
    assert normalize_value(0.1) == normalize_value(Decimal("0.10"))
    assert normalize_value(None) != normalize_value("")
    assert normalize_value(None) != normalize_value(0)
    assert normalize_value(b"ab") == normalize_value("ab")
    assert normalize_value(dt.datetime(2026, 10, 1, 0, 0)) == \
        normalize_value(dt.datetime(2026, 10, 1, 0, 0))


def test_correct_order_insensitive():
    user = set_(["a", "b"], [[1, "x"], [2, "y"]])
    ref = set_(["c", "d"], [[2, "y"], [1, "x"]])  # 列名不参与，顺序打乱
    assert grade(user, [ref]) == {"correct": True, "diffSummary": None}


def test_column_count_mismatch():
    r = grade(set_(["a"], [[1]]), [set_(["a", "b"], [[1, 2]])])
    assert r["correct"] is False
    assert "列数不符" in r["diffSummary"]


def test_missing_and_extra_rows():
    # 用户多出重复的 [1] 与游离的 [3]，共多 2 行；缺少 [2] 一行
    r = grade(set_(["a"], [[1], [1], [3]]), [set_(["a"], [[1], [2]])])
    assert r["correct"] is False
    assert "缺 1 行" in r["diffSummary"]
    assert "多 2 行" in r["diffSummary"]


def test_ordered_mode_checks_sequence():
    ref = set_(["a"], [[1], [2], [3]])
    shuffled = set_(["a"], [[3], [1], [2]])
    assert grade(shuffled, [ref], ordered=True)["correct"] is False
    assert grade(shuffled, [ref], ordered=False)["correct"] is True


def test_matches_any_reference_solution():
    # 多解汇总题：匹配任一参考结果集即判对
    method1 = set_(["user_id"], [[1], [3]])
    method2 = set_(["uid"], [[7], [9], [2]])
    user = set_(["x"], [[7], [2], [9]])
    assert grade(user, [method1, method2])["correct"] is True
