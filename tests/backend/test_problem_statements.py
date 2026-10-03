"""题面结构：三段模板、输出列、不可作答标注。"""

from data_builder.manifest import get_problem


def _output_columns(description: str) -> list[str]:
    output = description.split("## 输出", 1)[1]
    cols = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if not cells or cells[0] in {"列名", ""}:
            continue
        if set(cells[0]) <= set("-: "):
            continue
        cols.append(cells[0])
    return cols


def _assert_query(pid: str, columns: list[str], phrases: list[str]) -> None:
    text = get_problem(pid).description.strip()
    assert "English:" not in text, pid
    data_at = text.find("## 数据")
    rule_at = text.find("## 口径")
    out_at = text.find("## 输出")
    assert 0 <= data_at < rule_at < out_at, pid
    assert _output_columns(text) == columns, pid
    for phrase in phrases:
        assert phrase in text, f"{pid} 缺少 {phrase}"


def _assert_unsolvable(pid: str, sentence: str) -> None:
    text = get_problem(pid).description.strip()
    assert text.startswith("本题暂不可作答"), pid
    assert sentence in text, pid
    assert "## 输出" not in text, pid
    assert "English:" not in text, pid


def test_category_01_statements():
    _assert_query("01_01", ["user_id", "date1", "day_cnt"], ["大于 3", "至少 4 天"])
    _assert_query("01_02", ["user_id", "max_day_cnt"], ["最长连续天数", "没有「至少 N 天」"])
    _assert_query("01_03", ["user_id"], ["连续 3 天", "连续 4 天及以上"])
    _assert_unsolvable("01_04", "总结连续类 SQL 题的核心思路。")
    _assert_query("01_05", ["user_id", "grp", "consecutive_days"], ["balance > 1000", "大于 1"])
    _assert_query("01_06", ["user_id", "NAME", "start_date", "end_date"], ["次日"])
    _assert_query(
        "01_07",
        ["user_id", "streak_id", "streak_len"],
        ["result = 'win'", "每一段连续胜利"],
    )


def test_category_02_statements():
    _assert_query(
        "02_01",
        ["id", "ds", "price", "type"],
        ["持平"],
    )
    _assert_query(
        "02_02",
        ["id", "date", "value", "prev_value", "next_value"],
        ["前一行", "后一行"],
    )
    _assert_query(
        "02_03",
        ["date", "value", "prev_value", "change_pct"],
        ["2 位小数"],
    )


def test_category_03_statements():
    _assert_query(
        "03_01",
        ["student", "score", "rn", "rk", "dr"],
        ["row_number", "dense_rank"],
    )
    _assert_query(
        "03_02",
        ["student", "subject"],
        ["名次等于 2"],
    )


def test_category_04_early_statements():
    _assert_query(
        "04_01",
        ["user_id", "month_id", "visit_cnt_1m", "cumulative_visits"],
        ["visit_cnt_1m"],
    )
    _assert_query("04_02", ["room_id", "max_online"], ["2021-03-10"])
    _assert_query(
        "04_03",
        ["room_id", "hour_slot", "max_online"],
        ["前 13 个字符"],
    )
    _assert_query(
        "04_04",
        ["room_id", "hour_slot", "max_online"],
        ["不限制日期"],
    )


def test_category_04_late_statements():
    _assert_query(
        "04_05",
        ["room_id", "peak_time", "max_online"],
        ["2022-05-01", "并列最高"],
    )
    _assert_query("04_06", ["user_id", "reach_date"], ["大于等于 1000"])
    _assert_query("04_07", ["user_id", "product_id"], ["order_id"])
    _assert_query("04_08", ["id", "ds", "price"], ["严格低于"])


def test_category_05_06_statements():
    _assert_query("05_01", ["merged_start", "merged_end"], ["重叠"])
    _assert_query(
        "06_01",
        ["student_name", "class_name", "score"],
        ["score <= 60"],
    )
    _assert_query("06_02", ["u1", "u2"], ["(B,A)"])
    _assert_unsolvable("06_03", "当数据量达到千亿级别时，相互关注查询如何优化？")
