"""判题：用户末个结果集与参考答案各结果集的归一化比对"""

import datetime as dt
from collections import Counter
from decimal import Decimal


def normalize_value(v):
    """归一化为可哈希的类型标签值，消除表示差异（1 vs 1.0、b'a' vs 'a'）"""
    if v is None:
        return ("null", "")
    if isinstance(v, bool):
        return ("num", Decimal(int(v)))
    if isinstance(v, (int, float, Decimal)):
        return ("num", Decimal(str(v)))
    if isinstance(v, (bytes, bytearray)):
        return ("str", v.decode("utf-8", "replace"))
    if isinstance(v, dt.datetime):
        return ("dt", v.isoformat(" "))
    if isinstance(v, dt.date):
        return ("dt", v.isoformat())
    return ("str", str(v))


def _row_key(row) -> tuple:
    return tuple(normalize_value(v) for v in row)


def _multiset(rows) -> Counter:
    return Counter(_row_key(r) for r in rows)


def grade(user: dict, reference_sets: list[dict], ordered: bool = False) -> dict:
    """user 为用户最后一个结果集；reference_sets 为参考答案全部结果集。

    默认：列数相等 + 行多重集相等（顺序不敏感，列名不参与）。
    ordered=True：按行序列严格比对。
    匹配任一参考结果集即判对（多解汇总题）。
    """
    fallback = None
    for ref in reference_sets:
        if len(ref["columns"]) != len(user["columns"]):
            fallback = fallback or (
                f"列数不符（期望 {len(ref['columns'])} 列，"
                f"实际 {len(user['columns'])} 列）"
            )
            continue
        if ordered:
            if [_row_key(r) for r in user["rows"]] == \
                    [_row_key(r) for r in ref["rows"]]:
                return {"correct": True, "diffSummary": None}
            fallback = fallback or "行顺序不一致"
            continue
        miss = sum((_multiset(ref["rows"]) - _multiset(user["rows"])).values())
        extra = sum((_multiset(user["rows"]) - _multiset(ref["rows"])).values())
        if miss == 0 and extra == 0:
            return {"correct": True, "diffSummary": None}
        parts = []
        if miss:
            parts.append(f"缺 {miss} 行")
        if extra:
            parts.append(f"多 {extra} 行")
        fallback = fallback or " / ".join(parts)
    return {"correct": False, "diffSummary": fallback}
