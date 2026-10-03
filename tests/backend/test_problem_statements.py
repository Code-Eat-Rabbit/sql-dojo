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


def test_category_07_08_09_statements():
    _assert_query(
        "07_01",
        ["first_date", "day0_users", "day7_users", "retention_pct"],
        ["第 7 天"],
    )
    _assert_query("08_01", ["user_id", "tag"], ["按逗号拆开"])
    _assert_query("08_02", ["user_id", "tags"], ["先后不限"])
    _assert_query(
        "09_01",
        ["id", "status", "start_time", "end_time"],
        ["下一条"],
    )
    _assert_query(
        "09_02",
        ["id", "date", "value", "filled_value"],
        ["filled_value"],
    )


def test_category_10_11_statements():
    _assert_unsolvable(
        "10_01",
        "一些看似需要递归但实际可以用开窗函数解决的题目。典型场景：计算连续值、层级汇总等。",
    )
    text = get_problem("10_02").description.strip()
    assert "## 输出" not in text
    assert "English:" not in text
    for token in (
        "employee",
        "salary",
        "attendance",
        "emp_id",
        "dept_id",
        "base_salary",
        "check_in",
        "check_out",
    ):
        assert token in text, token
    _assert_query("11_01", ["date", "year"], ["前 4 个字符"])
    _assert_query("11_02", ["date", "quarter"], ["DIV 3"])
    _assert_unsolvable(
        "11_03",
        "汇总所有日期格式转换的代码：year, mm, quarter, half, h2t1, ytm, last*系列。",
    )


def test_category_12_13_14_statements():
    _assert_unsolvable("12_01", "字节跳动面试原题。")
    _assert_unsolvable("12_02", "字节跳动面试原题。")
    _assert_unsolvable("12_03", "得物真实业务场景 SQL 需求。")
    _assert_unsolvable("12_04", "阿里巴巴面试原题。")
    _assert_unsolvable("12_05", "拼多多面试原题。")
    _assert_query("13_01", ["id", "item"], ["$.items"])
    _assert_query("14_01", ["total_water"], ["total_water"])
    _assert_unsolvable("14_02", "墨天轮 SQL 挑战赛题目。")
    _assert_query(
        "14_03",
        ["horse", "time", "faster_horse"],
        ["全场最快"],
    )
    _assert_unsolvable("14_04", "如何用 SQL 计算块熵（Block Entropy）？")


def test_seeded_problem_text(client):
    detail = client.get("/api/problems/01_01")
    assert detail.status_code == 200
    assert "## 数据" in detail.json()["description"]
    assert detail.json()["title"] == "查询连续登陆3天以上的用户"

    stub = client.get("/api/problems/12_01")
    assert stub.status_code == 200
    assert stub.json()["description"].startswith("本题暂不可作答")
    assert stub.json()["title"] == "字节 — 题1"
