"""SQL 练习平台 — 元数据定义

集中管理所有专题、题目、表的映射关系。
data_builder 用此生成数据库，backend 用此提供 API。
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Problem:
    """一道 SQL 练习题。

    Attributes:
        id: 题目唯一标识，格式 "category_id_index"，如 "01_01"。
        category_id: 所属专题 ID，如 "01"。
        title: 题目标题。
        difficulty: 难度等级 1-5。
        tags: 标签列表，如 ["字节面试题", "row_number"]。
        description: 题目描述（Markdown 格式）。
        reference_sql: 参考答案（SQL 语句）。
        tables: 该题涉及的表名列表。
        hints: 解题提示列表。
        ordered: 判题是否要求行顺序一致。
    """
    id: str                # "01_01"
    category_id: str       # "01"
    title: str
    difficulty: int        # 1-5
    tags: List[str]
    description: str       # 题目描述（Markdown）
    reference_sql: str     # 参考答案（SQL）
    tables: List[str]      # 该题用到的表名
    hints: List[str]
    ordered: bool = False        # 判题是否要求行顺序一致（默认多重集比对）


@dataclass
class Category:
    """一个 SQL 练习专题，包含一组相关题目。

    Attributes:
        id: 专题唯一标识，如 "01"。
        name: 专题名称，如 "连续登陆"。
        db_file: 专题标识文件名（去掉 .db 后缀即 MySQL schema 名）。
        order: 排序序号。
        problems: 该专题包含的题目列表。
        knowledge: 分类知识点 Markdown，列表页顶部展示。
    """
    id: str
    name: str
    db_file: str           # "01_continuous_login.db"
    order: int
    problems: List[Problem]
    knowledge: str = ""    # 分类知识点（Markdown：解题思路/必背知识点/易错点）


# ============================================================
# 专题定义
# ============================================================
#
# CATEGORIES: 所有 SQL 练习专题的定义列表。
#   每个 Category 包含该专题的元数据及全部 Problem。
#   data_builder 遍历此列表生成数据库，backend 遍历此列表提供 API。

CATEGORIES: List[Category] = [
    Category(
        id="01",
        name="连续登陆 / Continuous Login",
        db_file="01_continuous_login.db",
        order=1,
        problems=[
            Problem(
                id="01_01",
                category_id="01",
                title="查询连续登陆3天以上的用户",
                difficulty=2,
                tags=["字节面试题", "row_number", "连续"],
                description="""
## 数据

表 `login_log`：`user_id`（用户），`login_date`（登录时间，字符串，可能带时分秒）。

## 口径

同一用户、同一天多次登录先按天去重（取 `login_date` 前 10 个字符）。再按用户把连续日期分成一段，只保留连续天数大于 3 的段（至少 4 天）。每一段一行。

## 输出

3 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| date1 | 连续段的分组键，同一段内相同 |
| day_cnt | 该段的连续天数 |
""",
                reference_sql="""
-- 步骤一：去重
SELECT user_id, substr(login_date, 1, 10) AS login_date
FROM login_log
GROUP BY user_id, substr(login_date, 1, 10);

-- 步骤二：用 row_number 标记分组（日期减去行号，连续日期得到相同 date1）
WITH numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM (
        SELECT user_id, SUBSTR(login_date, 1, 10) AS login_date
        FROM login_log
        GROUP BY user_id, SUBSTR(login_date, 1, 10)
    ) dedup
)
SELECT user_id, login_date,
       DATE_ADD(login_date, INTERVAL -rn DAY) AS date1
FROM numbered;

-- 步骤三：统计连续天数
WITH numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM (
        SELECT user_id, SUBSTR(login_date, 1, 10) AS login_date
        FROM login_log
        GROUP BY user_id, SUBSTR(login_date, 1, 10)
    ) dedup
),
flagged AS (
    SELECT user_id, DATE_ADD(login_date, INTERVAL -rn DAY) AS date1
    FROM numbered
)
SELECT user_id, date1, COUNT(*) AS day_cnt
FROM flagged
GROUP BY user_id, date1
HAVING COUNT(*) > 3;
""",
                tables=["login_log"],
                hints=[
                    "思路：row_number() over() 减一下，再分组 count",
                    "步骤一先去重，步骤二用 date_add + row_number 创建分组标识",
                    "步骤三按分组标识 count，筛选 count > 3"
                ],
            ),
            Problem(
                id="01_02",
                category_id="01",
                title="查询连续登陆最大天数用户",
                difficulty=2,
                tags=["字节面试题", "row_number", "连续", "max"],
                description="""
## 数据

表 `login_log`：`user_id`（用户），`login_date`（登录时间，字符串，可能带时分秒）。

## 口径

同一用户、同一天多次登录先按天去重。按用户把连续日期分成一段，再对每个用户取这些段里的最长连续天数。每个有登录记录的用户一行，没有「至少 N 天」的筛选。

## 输出

2 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| max_day_cnt | 该用户的最长连续登录天数 |
""",
                reference_sql="""
-- 承接 01_01 的思路：去重 → row_number 差值分组 → 按用户取最大连续天数
WITH dedup AS (
    SELECT user_id, SUBSTR(login_date, 1, 10) AS login_date
    FROM login_log
    GROUP BY user_id, SUBSTR(login_date, 1, 10)
),
numbered AS (
    SELECT user_id, login_date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
    FROM dedup
),
flagged AS (
    SELECT user_id, DATE_ADD(login_date, INTERVAL -rn DAY) AS date1
    FROM numbered
),
day_cnt AS (
    SELECT user_id, date1, COUNT(*) AS day_cnt
    FROM flagged
    GROUP BY user_id, date1
)
SELECT user_id, MAX(day_cnt) AS max_day_cnt
FROM day_cnt
GROUP BY user_id;
""",
                tables=["login_log"],
                hints=[
                    "承接上一题的思路",
                    "在第三步基础上再套一层 max"
                ],
            ),
            Problem(
                id="01_03",
                category_id="01",
                title="连续登录3天以上用户 — 三种方法汇总",
                difficulty=3,
                tags=["row_number", "连续", "方法汇总"],
                description="""
## 数据

表 `login_log`：`user_id`（用户），`login_date`（登录时间，字符串，可能带时分秒）。

## 口径

同一用户、同一天多次登录先按天去重。找出存在连续 3 天登录的用户：某一天、它的前 1 天、前 2 天都有登录。连续 4 天及以上的用户也包含在内。每个用户只出现一次。

## 输出

1 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
""",
                reference_sql="""
-- 方法1: row_number()
-- （同 01_01）

-- 方法2: lag()
SELECT DISTINCT user_id
FROM (
    SELECT user_id, login_date,
           LAG(login_date, 1) OVER (PARTITION BY user_id ORDER BY login_date) AS prev1,
           LAG(login_date, 2) OVER (PARTITION BY user_id ORDER BY login_date) AS prev2
    FROM (SELECT user_id, substr(login_date,1,10) AS login_date FROM login_log GROUP BY user_id, substr(login_date,1,10)) AS d
) t
WHERE DATEDIFF(login_date, prev1) = 1 AND DATEDIFF(prev1, prev2) = 1;

-- 方法3: 自关联
SELECT DISTINCT a.user_id
FROM (SELECT user_id, substr(login_date,1,10) AS login_date FROM login_log GROUP BY user_id, substr(login_date,1,10)) a
JOIN (SELECT user_id, substr(login_date,1,10) AS login_date FROM login_log GROUP BY user_id, substr(login_date,1,10)) b
  ON a.user_id = b.user_id AND DATEDIFF(a.login_date, b.login_date) = 1
JOIN (SELECT user_id, substr(login_date,1,10) AS login_date FROM login_log GROUP BY user_id, substr(login_date,1,10)) c
  ON b.user_id = c.user_id AND DATEDIFF(b.login_date, c.login_date) = 1;
""",
                tables=["login_log"],
                hints=[
                    "三种方法核心都是找到连续日期",
                    "row_number 法最通用，建议重点掌握",
                ],
            ),
            Problem(
                id="01_04",
                category_id="01",
                title="总结：连续类题的思路",
                difficulty=1,
                tags=["连续", "总结"],
                description="""
本题暂不可作答。

总结连续类 SQL 题的核心思路。
""",
                reference_sql="""
-- 核心思路：row_number() over() 减一下，再分组 count
-- 适用场景：连续登录、连续签到、连续下单等
""",
                tables=[],
                hints=[
                    "row_number() over(partition by id order by date)",
                    "date_sub/date_add 创建一个基准日期",
                    "按基准日期分组 count"
                ],
            ),
            Problem(
                id="01_05",
                category_id="01",
                title="拓展1：用户账户余额大于1000的连续天数",
                difficulty=3,
                tags=["连续", "外汇", "条件筛选"],
                description="""
## 数据

表 `account`：`user_id`（用户），`date`（日期），`balance`（账户余额）。

## 口径

先保留 `balance > 1000` 的行。再按用户把连续日期分成一段，只输出长度大于 1 的段。每一段一行。

## 输出

3 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| grp | 连续段的分组键，同一段内相同 |
| consecutive_days | 该段的连续天数 |
""",
                reference_sql="""
-- 先筛选余额 > 1000 的行，再套用连续类题的思路
WITH filtered AS (
    SELECT user_id, date, balance
    FROM account
    WHERE balance > 1000
),
numbered AS (
    SELECT user_id, date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) AS rn
    FROM filtered
),
flagged AS (
    SELECT user_id,
           DATE_SUB(date, INTERVAL rn DAY) AS grp
    FROM numbered
)
SELECT user_id, grp, COUNT(*) AS consecutive_days
FROM flagged
GROUP BY user_id, grp
HAVING COUNT(*) > 1;
""",
                tables=["account"],
                hints=[
                    "先 WHERE 过滤再做连续判断",
                    "WHERE balance > 1000 放在子查询里"
                ],
            ),
            Problem(
                id="01_06",
                category_id="01",
                title="拓展2：日期连续（集度面试题）",
                difficulty=4,
                tags=["连续", "集度", "日期区间合并"],
                description="""
## 数据

表 `user_schedule`：`user_id`（用户），`name`（姓名），`start_date`（区间开始日），`end_date`（区间结束日）。

## 口径

按 `user_id` 与 `name` 分组，组内按 `start_date` 排序。仅当下一段的 `start_date` 恰好等于上一段 `end_date` 的次日时，两段并入同一组。重叠但不满足这个次日条件的区间各自成段。每一组输出最早的开始日和最晚的结束日。

## 输出

4 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| NAME | 姓名 |
| start_date | 该段最早的开始日 |
| end_date | 该段最晚的结束日 |
""",
                reference_sql="""
WITH t1 AS (
    SELECT user_id, NAME, start_date, end_date,
           LAG(end_date) OVER (PARTITION BY user_id, NAME ORDER BY start_date) AS lag_date,
           CASE
               WHEN DATE_ADD(LAG(end_date) OVER (PARTITION BY user_id, NAME ORDER BY start_date), INTERVAL 1 DAY) = start_date
               THEN 0 ELSE 1
           END AS new_group_flag
    FROM user_schedule
),
t2 AS (
    SELECT user_id, NAME, start_date, end_date,
           SUM(new_group_flag) OVER (PARTITION BY user_id, NAME ORDER BY start_date) AS group_id
    FROM t1
)
SELECT user_id, NAME,
       MIN(start_date) AS start_date,
       MAX(end_date) AS end_date
FROM t2
GROUP BY user_id, NAME, group_id
ORDER BY MIN(start_date), user_id, NAME;
""",
                tables=["user_schedule"],
                hints=[
                    "先判断相邻两行是否连续（lag 比较）",
                    "用 SUM(new_group_flag) 累加创建分组号",
                    "最后按分组号聚合取 min(start), max(end)"
                ],
            ),
            Problem(
                id="01_07",
                category_id="01",
                title="拓展3：连胜数",
                difficulty=3,
                tags=["连续", "胜负"],
                description="""
## 数据

表 `games`：`user_id`（用户），`date`（日期），`result`（结果，胜利为 `win`）。

## 口径

只看 `result = 'win'` 的记录。按用户、按日期把连续的胜利分成段。每一段连续胜利一行，包含长度为 1 的段。没有胜利的用户不出现。

## 输出

3 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| streak_id | 连胜段的分组键 |
| streak_len | 该段的胜利场数 |
""",
                reference_sql="""
-- 解法1：先把胜负转 0/1，再套连续类题思路
WITH numbered AS (
    SELECT user_id, date, result,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) AS rn,
           ROW_NUMBER() OVER (PARTITION BY user_id, result ORDER BY date) AS rn2
    FROM games
    WHERE result = 'win'
)
SELECT user_id, MAX(streak) AS max_streak
FROM (
    SELECT user_id, rn - rn2 AS grp, COUNT(*) AS streak
    FROM numbered
    GROUP BY user_id, grp
) t
GROUP BY user_id;

-- 解法2：用 lag 判断是否连续胜
WITH marked AS (
    SELECT user_id, date, result,
           CASE WHEN result = 'win' AND LAG(result) OVER (PARTITION BY user_id ORDER BY date) = 'win'
                THEN 0 ELSE 1 END AS new_streak
    FROM games
),
streaks AS (
    SELECT user_id,
           SUM(new_streak) OVER (PARTITION BY user_id ORDER BY date) AS streak_id
    FROM marked
    WHERE result = 'win'
)
SELECT user_id, streak_id, COUNT(*) AS streak_len
FROM streaks
GROUP BY user_id, streak_id;
""",
                tables=["games"],
                hints=[
                    "连续类题的变体：把'连续'条件从日期改为胜负状态",
                    "关键：把 win 的行单独拎出来，然后用 row_number 差值法"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **差值法（首选）**：去重 → `日期 - row_number()` 得分组键 → `GROUP BY` + `HAVING` 计数。连续日期减去递增行号会得到相同常量，即分组键。
- **lag 法**：`lag` 取前 N-1 个日期，`datediff` 全差 1 则连续——每个日期都与它前面 N-1 天对齐比较。
- **自关联法**：自关联 N 次（同表 join，a/b 别名），`datediff = 1` 逐级衔接。
- **条件连续（连胜类）**：先筛出满足条件的行 → 双 `row_number` 差值分组，或 `lag + case` 造断点标记 + `sum() over` 累加分段。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `row_number()` | 严格递增 1,2,3,4，并列也分先后 | 去重取一名 / 差值法分组键 |
| `rank()` | 并列同号，下一个跳号 1,2,2,4 | 要名次跳号时用 |
| `dense_rank()` | 并列同号，下一个不跳 1,2,2,3 | 不跳号场景 |
| `datediff(a, b)` | 返回 a-b 的天数 | 注意参数方向，是 a 减 b |
| `date_add(d, n)` / `date_sub(d, n)` | 日期增减 n 天 | n 可为负数 |
| `substr(date, 1, 10)` | 取日期部分（去时分秒） | 等价 `to_date()`（Hive/Spark；MySQL 无此函数，用 SUBSTR） |

## 易错点

- 排号前**必须先去重**（按人 + 按天 GROUP BY）：同日多次登录会产生重复日期，打断连续判定。
- `NOT IN` 子查询结果含 NULL 时整体返回空——规避：`NOT EXISTS` 或子查询加 `WHERE col IS NOT NULL`。
""",
    ),
    Category(
        id="02",
        name="开窗函数 lead/lag / Window Functions lead/lag",
        db_file="02_window_lead_lag.db",
        order=2,
        problems=[
            Problem(
                id="02_01",
                category_id="02",
                title="波峰波谷",
                difficulty=3,
                tags=["lead", "lag", "波峰波谷"],
                description="""
## 数据

表 `stock_price`：`id`（标的），`ds`（日期），`price`（价格）。

## 口径

按 `id` 分组、按 `ds` 排序。某一天的价格同时大于前一天和后一天，记为「波峰」；同时小于前一天和后一天，记为「波谷」。其余情况（含缺少前一天或后一天）记为「持平」。每一行价格记录都输出。

## 输出

4 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| id | 标的 |
| ds | 日期 |
| price | 价格 |
| type | 波峰、波谷或持平 |
""",
                reference_sql="""
SELECT id, ds, price,
       CASE WHEN price > lag_price AND price > lead_price THEN '波峰'
            WHEN price < lag_price AND price < lead_price THEN '波谷'
            ELSE '持平' END AS type
FROM (
    SELECT id, ds, price,
           LAG(price) OVER (PARTITION BY id ORDER BY ds) AS lag_price,
           LEAD(price) OVER (PARTITION BY id ORDER BY ds) AS lead_price
    FROM stock_price
) t;
""",
                tables=["stock_price"],
                hints=[
                    "lag 看前一天，lead 看后一天",
                    "用 case when 判断"
                ],
            ),
            Problem(
                id="02_02",
                category_id="02",
                title="拓展1：前后列转换",
                difficulty=2,
                tags=["lag", "列转换"],
                description="""
## 数据

表 `metric_readings`：`id`（分组），`date`（日期），`value`（数值）。

## 口径

按 `id` 分组、按 `date` 排序。每一行带上同一组里前一行和后一行的 `value`。该组第一行的前值为空，最后一行的后值为空。

## 输出

5 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| id | 分组 |
| date | 日期 |
| value | 当前值 |
| prev_value | 前一行的值 |
| next_value | 后一行的值 |
""",
                reference_sql="""
SELECT id, date, value,
       LAG(value) OVER (PARTITION BY id ORDER BY date) AS prev_value,
       LEAD(value) OVER (PARTITION BY id ORDER BY date) AS next_value
FROM metric_readings;
""",
                tables=["metric_readings"],
                hints=[
                    "lag(col, 1) → 上一行",
                    "lead(col, 1) → 下一行",
                ],
            ),
            Problem(
                id="02_03",
                category_id="02",
                title="拓展2：真实面试题",
                difficulty=3,
                tags=["lag", "面试"],
                description="""
## 数据

表 `metrics`：`date`（日期），`value`（数值）。

## 口径

全表按 `date` 排序。每一行给出前一行的 `value`，以及相对前一行的百分比变化：`(当前值 - 前值) * 100 / 前值`，保留 2 位小数。第一行的前值和变化率为空。

## 输出

4 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| date | 日期 |
| value | 当前值 |
| prev_value | 前一行的值 |
| change_pct | 相对前一行的百分比变化，保留 2 位小数 |
""",
                reference_sql="""
-- 面试题典型场景：计算变化率
SELECT date, value,
       LAG(value) OVER (ORDER BY date) AS prev_value,
       ROUND((value - LAG(value) OVER (ORDER BY date)) * 100.0 / LAG(value) OVER (ORDER BY date), 2) AS change_pct
FROM metrics;
""",
                tables=["metrics"],
                hints=[
                    "lag 取前值，计算差值/变化率"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **波峰波谷**：`lag` 取前值 + `lead` 取后值 + `case when` 三比较——同时大于（或小于）前后两行即为波峰（波谷）。
- **环比变化率**：`lag` 取前值 → `(今 - 前) / 前` → `round` 保留位数。
- **前后列转换**：`lag`/`lead` 取上/下一行的值"放到当前行当列用"，本质是把行间关系变成行内比较。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `lag(col, n, default)` | 向上取第 n 行的 col 值 | default 可省，首行补 NULL/默认值 |
| `lead(col, n, default)` | 向下取第 n 行的 col 值 | 与 lag 方向相反 |
| `first_value(col)` | 窗口帧内第一个值 | 注意帧范围影响结果 |
| `last_value(col)` | 窗口帧内最后一个值 | 默认帧不含后续行，易错 |
| `OVER(PARTITION BY ... ORDER BY ...)` | 窗口结构：分组 + 组内排序 | lag/lead 必须配 ORDER BY |

## 易错点

- `lag`/`lead` 不写 `ORDER BY` 会报错或结果无意义。
- `last_value` 默认帧是 `RANGE ... CURRENT ROW`，不含后续行——要取组尾须显式写 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`。
""",
    ),
    Category(
        id="03",
        name="三种排序开窗 / Three Ranking Window Functions",
        db_file="03_window_rank.db",
        order=3,
        problems=[
            Problem(
                id="03_01",
                category_id="03",
                title="三种排序开窗：row_number / rank / dense_rank",
                difficulty=2,
                tags=["row_number", "rank", "dense_rank", "topN"],
                description="""
## 数据

表 `scores`：`student`（学生），`score`（分数）。

## 口径

全表按 `score` 从高到低排序，为每一行同时计算三种名次：`row_number`（严格递增）、`rank`（并列后跳号）、`dense_rank`（并列后不跳号）。

## 输出

5 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| student | 学生 |
| score | 分数 |
| rn | row_number 名次 |
| rk | rank 名次 |
| dr | dense_rank 名次 |
""",
                reference_sql="""
SELECT student, score,
       ROW_NUMBER() OVER (ORDER BY score DESC) AS rn,
       RANK() OVER (ORDER BY score DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY score DESC) AS dr
FROM scores;
""",
                tables=["scores"],
                hints=[
                    "row_number: 1,2,3,4 严格递增",
                    "rank: 1,2,2,4 跳跃",
                    "dense_rank: 1,2,2,3 不跳跃"
                ],
            ),
            Problem(
                id="03_02",
                category_id="03",
                title="每个学生成绩第二高的科目",
                difficulty=3,
                tags=["dense_rank", "topN", "面试"],
                description="""
## 数据

表 `student_scores`：`student`（学生），`subject`（科目），`score`（分数）。

## 口径

按学生分组，组内按分数从高到低做 `dense_rank`。只保留名次等于 2 的行。并列第二的科目都保留。不输出分数。没有第二名次的学生不出现。

## 输出

2 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| student | 学生 |
| subject | 科目 |
""",
                reference_sql="""
SELECT student, subject
FROM (
    SELECT student, subject, score,
           DENSE_RANK() OVER (PARTITION BY student ORDER BY score DESC) AS dr
    FROM student_scores
) t
WHERE dr = 2;
""",
                tables=["student_scores"],
                hints=[
                    "partition by student 分组排序",
                    "dense_rank 保证并列第二也被取到",
                    "取 dr = 2 即可"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **TopN**：`row_number()` 并列也分先后——每组取第一名时并列只留一个，天然去重。
- **第 N 高**：`dense_rank() over(partition by ... order by ... desc)` 取 `= N`——并列不跳号，保证第 N 高语义正确。
- **选型口诀**：要名次跳号用 `rank`；不跳号/取第 N 高用 `dense_rank`；TopN 去重用 `row_number`。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `row_number()` | 严格递增 1,2,3,4（并列也分先后） | TopN 去重取一名 |
| `rank()` | 并列同号，下一个跳号 1,2,2,4 | 要名次跳号时用 |
| `dense_rank()` | 并列同号，下一个不跳 1,2,2,3 | 取第 N 高必用 |
| `OVER(PARTITION BY ... ORDER BY ...)` | 分组 + 组内排序 | 排序方向决定"第 N 高/低" |

## 易错点

- 求"第 N 高"用 `row_number` 会把并列值拆成不同名次，导致漏解；必须用 `dense_rank`。
- 对比"全体第 N"与"每组第 N"：不加 `PARTITION BY` 是全局排名，加了才是组内排名。
""",
    ),
    Category(
        id="04",
        name="累计汇总 / Cumulative Aggregation",
        db_file="04_cumulative_agg.db",
        order=4,
        problems=[
            Problem(
                id="04_01",
                category_id="04",
                title="统计每个用户累计访问次数",
                difficulty=2,
                tags=["sum", "累计", "聚合开窗"],
                description="""
## 数据

表 `user_visits`：`user_id`（用户），`month_id`（月份，形如 `2024-01`），`visit_cnt_1m`（该月访问次数）。

## 口径

按用户分组，组内按 `month_id` 排序，对 `visit_cnt_1m` 做从早到晚的累计。每个用户的每个月一行。

## 输出

4 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| user_id | 用户 |
| month_id | 月份 |
| visit_cnt_1m | 该月访问次数 |
| cumulative_visits | 截至该月的累计访问次数 |
""",
                reference_sql="""
SELECT user_id, month_id, visit_cnt_1m,
       SUM(visit_cnt_1m) OVER (PARTITION BY user_id ORDER BY month_id) AS cumulative_visits
FROM user_visits;
""",
                tables=["user_visits"],
                hints=[
                    "sum(col) over(partition by ... order by ...) 实现累计",
                    "不加 order by 则是全局总和"
                ],
            ),
            Problem(
                id="04_02",
                category_id="04",
                title="同时在线人数",
                difficulty=3,
                tags=["同时在线", "进出时间", "累加"],
                description="""
## 数据

表 `live_log`：`room_id`（直播间），`user_id`（用户），`login_time`（进入时间），`logout_time`（离开时间）。

## 口径

登录事件只保留 `login_time` 落在 `2021-03-10` 的行，记为 +1。离开事件只保留 `logout_time` 落在 `2021-03-10` 的行，记为 -1。按房间、按事件时间累加，得到每个事件之后的在线人数。每个房间取这个在线人数的最大值。

## 输出

2 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| room_id | 直播间 |
| max_online | 该日在线人数的最大值 |
""",
                reference_sql="""
-- 步骤一：进入+1，离开-1
SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
WHERE SUBSTR(login_time, 1, 10) = '2021-03-10'
UNION ALL
SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
WHERE SUBSTR(logout_time, 1, 10) = '2021-03-10';

-- 步骤二：按时间累加
SELECT room_id, event_time,
       SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
FROM (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE SUBSTR(login_time, 1, 10) = '2021-03-10'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE SUBSTR(logout_time, 1, 10) = '2021-03-10'
) events;

-- 步骤三：取最大值
SELECT room_id, MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        WHERE SUBSTR(login_time, 1, 10) = '2021-03-10'
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
        WHERE SUBSTR(logout_time, 1, 10) = '2021-03-10'
    ) events
) online
GROUP BY room_id;
""",
                tables=["live_log"],
                hints=[
                    "进入+1，离开-1，按时间排序累加",
                    "用 union all 把进出事件合并",
                ],
            ),
            Problem(
                id="04_03",
                category_id="04",
                title="拓展1：每小时内的同时在线人数",
                difficulty=3,
                tags=["同时在线", "小时"],
                description="""
## 数据

表 `live_log`：`room_id`（直播间），`user_id`（用户），`login_time`（进入时间），`logout_time`（离开时间）。

## 口径

登录只保留 `login_time` 在 `2021-03-10` 的行（+1），离开只保留 `logout_time` 在该日的行（-1），按房间按时间累加。再按事件时间的前 13 个字符（到小时）分组，取该小时内出现过的最大在线人数。累加跨小时连续计算，不在每个小时重新从 0 开始。

## 输出

3 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| room_id | 直播间 |
| hour_slot | 小时，取事件时间的前 13 个字符 |
| max_online | 该小时内出现过的最大在线人数 |
""",
                reference_sql="""
-- 在步骤二的 event_time 上加 SUBSTR 取小时粒度即可
SELECT room_id, SUBSTR(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        WHERE SUBSTR(login_time, 1, 10) = '2021-03-10'
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
        WHERE SUBSTR(logout_time, 1, 10) = '2021-03-10'
    ) events
) online
GROUP BY room_id, SUBSTR(event_time, 1, 13);
""",
                tables=["live_log"],
                hints=[
                    "在原来基础上加 hour 分组即可"
                ],
            ),
            Problem(
                id="04_04",
                category_id="04",
                title="拓展2：不限制时段的同时在线人数",
                difficulty=2,
                tags=["同时在线", "全时段"],
                description="""
## 数据

表 `live_log`：`room_id`（直播间），`user_id`（用户），`login_time`（进入时间），`logout_time`（离开时间）。

## 口径

不限制日期。进入记 +1，离开记 -1，按房间按时间对全部历史累加。再按事件时间的前 13 个字符（到小时）分组，取该小时内出现过的最大在线人数。累加跨小时、跨日期连续计算。

## 输出

3 列，行顺序不限。

| 列名 | 含义 |
|---|---|
| room_id | 直播间 |
| hour_slot | 小时，取事件时间的前 13 个字符 |
| max_online | 该小时内出现过的最大在线人数 |
""",
                reference_sql="""
-- 去掉 WHERE 日期筛选即可
SELECT room_id, SUBSTR(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    ) events
) online
GROUP BY room_id, SUBSTR(event_time, 1, 13);
""",
                tables=["live_log"],
                hints=[
                    "去掉日期限制即可"
                ],
            ),
            Problem(
                id="04_05",
                category_id="04",
                title="拓展3：直播间最大在线观看人数及时间",
                difficulty=4,
                tags=["同时在线", "峰值时间"],
                description="""
统计 2022-05-01 当天每个直播间最大在线观看人数，以及达到该峰值的时间。

English: For a specific date, find the maximum concurrent viewer count per live room and the exact time when that peak occurred. Use cumulative sum + rank.
""",
                reference_sql="""
WITH events AS (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE substr(login_time, 1, 10) = '2022-05-01'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE substr(logout_time, 1, 10) = '2022-05-01'
),
cumulative AS (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time, user_type) AS online_cnt
    FROM events
)
SELECT room_id, event_time AS peak_time, online_cnt AS max_online
FROM (
    SELECT room_id, event_time, online_cnt,
           RANK() OVER (PARTITION BY room_id ORDER BY online_cnt DESC) AS rk
    FROM cumulative
) t
WHERE rk = 1;
""",
                tables=["live_log"],
                hints=[
                    "先算在线人数，再用 rank 取每个房间的峰值行",
                ],
            ),
            Problem(
                id="04_06",
                category_id="04",
                title="拓展4：求最小达到某累计金额的日期",
                difficulty=5,
                tags=["累计", "hard", "美团"],
                description="""
给定每个用户每天的消费金额，求每个用户累计消费首次达到 1000 元的日期。

English: Given daily spending per user, find the earliest date when each user's cumulative spending first reaches 1000. Use cumulative sum, filter, then MIN.
""",
                reference_sql="""
WITH cumulative AS (
    SELECT user_id, dt, price,
           SUM(price) OVER (PARTITION BY user_id ORDER BY dt) AS cum_price
    FROM user_spend
)
SELECT user_id, MIN(dt) AS reach_date
FROM cumulative
WHERE cum_price >= 1000
GROUP BY user_id;
""",
                tables=["user_spend"],
                hints=[
                    "先累加，再 where 筛选，最后 min 取最早日期"
                ],
            ),
            Problem(
                id="04_07",
                category_id="04",
                title="拓展5：商品复购",
                difficulty=4,
                tags=["复购", "累计"],
                description="""
计算每个用户复购（购买了 ≥ 2 次）的商品列表。

English: Find products that each user has purchased 2 or more times (repurchase analysis). Use GROUP BY + HAVING COUNT >= 2.
""",
                reference_sql="""
SELECT user_id, product_id
FROM orders
GROUP BY user_id, product_id
HAVING COUNT(DISTINCT order_id) >= 2;
""",
                tables=["orders"],
                hints=["group by + having count >= 2"],
            ),
            Problem(
                id="04_08",
                category_id="04",
                title="拓展6：历史新低的商品",
                difficulty=3,
                tags=["新低", "累计", "min"],
                description="""
找出当天价格是历史新低的商品 ID。

English: Find products whose price today is an all-time low. Use `min() over()` for a rolling minimum, then compare current price with historical minimum.
""",
                reference_sql="""
WITH min_so_far AS (
    SELECT id, ds, price,
           MIN(price) OVER (PARTITION BY id ORDER BY ds) AS min_price_so_far,
           LAG(price) OVER (PARTITION BY id ORDER BY ds) AS prev_price
    FROM product_price
)
SELECT id, ds, price
FROM min_so_far
WHERE price = min_price_so_far
  AND price < prev_price;
""",
                tables=["product_price"],
                hints=[
                    "min(price) over(partition by id order by ds) 实现滚动最小值",
                ],
            ),
        ],
        knowledge="""## 解题思路

- **核心口诀**：`sum() over` 加 `ORDER BY` = 累计；不加 = 分组总量。
- **同时在线**：进 +1 / 出 -1 → `union all` → `sum() over` 累加 → `max` 取峰值。事件按时间排序后累加差值即为瞬时在线人数。
- **首次达标**：累计后 `where` 筛 + `min(日期)`——先算累计列，外层筛出达到阈值的行，再取最早日期。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `sum/min/max/avg/count(col) OVER(...)` | 聚合开窗 | 加 ORDER BY = 累计；不加 = 分组总量 |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | 明确框定累计范围（组首到当前行） | 显式写帧最稳 |
| 默认帧规则 | 有 ORDER BY 为 `RANGE ... CURRENT ROW`；无 ORDER BY 为全组 | 同值会并入同一帧 |
| ROWS vs RANGE | ROWS 按物理行；RANGE 按排序值（同值并入同一帧） | 日期去重后两者等价 |

## 易错点

- 同时在线题必须 `union all` 不能 `union`：`union` 去重会把同值 +1/-1 行合并，破坏计数。
- 默认帧是 RANGE 时，排序列有重复值会把同值行并入同一帧，累计值跳变——需要逐行累计时显式用 `ROWS`。
""",
    ),
    Category(
        id="05",
        name="炸裂函数 / Explode Functions",
        db_file="05_explode.db",
        order=5,
        problems=[
            Problem(
                id="05_01",
                category_id="05",
                title="区间交集 — 合并区间",
                difficulty=4,
                tags=["explode", "区间", "合并"],
                description="""
给定多个区间（start, end），合并所有有交集的区间。

English: Given multiple intervals (start, end), merge all overlapping intervals. Use MAX(end) over() as a rolling maximum and detect non-overlapping groups.
""",
                reference_sql="""
WITH intervals AS (
    SELECT start, end,
           MAX(end) OVER (ORDER BY start ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS max_end_so_far,
           CASE WHEN start > MAX(end) OVER (ORDER BY start ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
                THEN 1 ELSE 0 END AS new_group
    FROM raw_intervals
),
grouped AS (
    SELECT start, end, SUM(new_group) OVER (ORDER BY start) AS group_id
    FROM intervals
)
SELECT MIN(start) AS merged_start, MAX(end) AS merged_end
FROM grouped
GROUP BY group_id;
""",
                tables=["raw_intervals"],
                hints=[
                    "用 max(end) over() 滚动获取之前的最大 end",
                    "start > 之前的 max_end 则开启新区间",
                ],
            ),
        ],
        knowledge="""## 解题思路

- **行转列（一行变多行）**：Hive 用 `lateral view explode(split(col, ','))`——先 split 成数组，再 explode 炸成多行。
- **MySQL 8 替代**：用 `JSON_TABLE` 把数组展开为行，或递归 CTE 逐行拆分（见 13 系 JSON 题的语法骨架）。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `split(s, ',')` | 按分隔符切分成数组 | Hive/Spark |
| `explode` | 数组炸裂：一行变多行 | 每个数组元素一行 |
| `lateral view` | 配合 explode 的表生成函数写法 | 位置在 FROM 之后、WHERE 之前 |
| `JSON_TABLE(col, '$.items[*]' COLUMNS (...))` | MySQL 8 表函数，JSON 数组展开 | 需与主表逗号连用 |
| 递归 CTE | `WITH RECURSIVE` 逐层拆字符串 | MySQL 8 无 lateral view 的替代 |

JSON_TABLE 完整示例骨架（MySQL 8）：

```sql
SELECT t.user_id, jt.item
FROM user_tags t,
     JSON_TABLE(CONCAT('[', t.tags, ']'), '$[*]'
         COLUMNS (item VARCHAR(64) PATH '$')) AS jt;
```

递归 CTE 思路（一句话）：锚定查询先给每行放全串，递归部分反复 `SUBSTR + INSTR` 截下第一个元素、把余串传给下一轮，直到余串为空——即模拟 explode。

`lateral view` 位置规则展开：写法是 `FROM 表 [别名] lateral view explode(...) 别名 AS 列名`，必须紧跟它作用的表之后；多列同时炸裂可叠多个 lateral view（各产生一行，行数做笛卡尔积）。

## 易错点

- `lateral view` 必须紧跟包含它的表之后（FROM 之后、WHERE 之前），写错位置直接语法报错。
- 空串切分也会产生一行（split 空串得到一个元素的数组），展开前先过滤空值。
""",
    ),
    Category(
        id="06",
        name="关联应用 / Join Applications",
        db_file="06_joins.db",
        order=6,
        problems=[
            Problem(
                id="06_01",
                category_id="06",
                title="每一门课大于60分的学生的所有科目成绩",
                difficulty=3,
                tags=["子查询", "join", "关联"],
                description="""
查询「所有科目都大于 60 分」的学生的全部成绩记录。

English: Find all score records for students who scored above 60 in every subject. Use NOT IN to exclude students with any failing score, then JOIN to get full records.
""",
                reference_sql="""
SELECT t0.student_name, t2.class_name, t1.score
FROM student t0
JOIN sc t1 ON t0.id = t1.sid
JOIN class t2 ON t1.cid = t2.id
WHERE t0.id NOT IN (
    SELECT sid FROM sc WHERE score <= 60
);
""",
                tables=["student", "sc", "class"],
                hints=[
                    "NOT IN 排除有不及格科目的学生",
                    "再用 JOIN 查出这些学生全部科目和成绩"
                ],
            ),
            Problem(
                id="06_02",
                category_id="06",
                title="相互关注（共同好友）",
                difficulty=3,
                tags=["自关联", "join", "相互关注"],
                description="""
在关注关系表 `fans(from_user, to_user)` 中，找出相互关注的用户对。

English: In a follow-relationship table (from_user, to_user), find mutual follow pairs. Two approaches: self-join or UNION + GROUP BY HAVING COUNT >= 2.
""",
                reference_sql="""
-- 方法1：JOIN
SELECT a.from_user AS u1, a.to_user AS u2
FROM fans a
JOIN fans b ON a.from_user = b.to_user AND a.to_user = b.from_user
WHERE a.from_user < a.to_user;

-- 方法2：UNION + GROUP
SELECT u1, u2 FROM (
    SELECT from_user AS u1, to_user AS u2 FROM fans
    UNION ALL
    SELECT to_user AS u1, from_user AS u2 FROM fans
) t
GROUP BY u1, u2
HAVING COUNT(*) >= 2;
""",
                tables=["fans"],
                hints=[
                    "方法1: 自关联，a关注b 且 b关注a",
                    "方法2: union 后 group by having count >= 2"
                ],
            ),
            Problem(
                id="06_03",
                category_id="06",
                title="引申优化：千亿级数据共同好友",
                difficulty=5,
                tags=["优化", "千亿", "大数据"],
                description="""
当数据量达到千亿级别时，相互关注查询如何优化？

English: How to optimize mutual-follow queries at billion-row scale? Discussion of map-side joins, bucketing, and Bloom filters to avoid full shuffle joins.
""",
                reference_sql="""
-- 思路：不再用 JOIN，而是用 map 端 join（小表放内存）
-- 或使用桶表（bucket）让相同用户的数据落在同一节点
-- 或用 Bloom filter 快速排除不可能相互关注的用户
""",
                tables=[],
                hints=[
                    "大数据场景下的优化思路而非具体 SQL",
                    "关键：避免全量 shuffle join"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **全称量词（每科都 > 60）**：双重否定——`not in`（存在不及格的学生）；或 `group by` + `having min(score) > 60`。"都满足" = "不存在不满足"。
- **相互关注**：自关联 `a.from = b.to and a.to = b.from`；或 `union all` 双向展开 + `having count >= 2`。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `inner join` | 只留两边都匹配的行 | 常规匹配 |
| `left join` | 保左表全量，右表缺失补 NULL | 保分母不丢（留存题关键） |
| `full outer join` | 两边全保 | MySQL 8 不直接支持，用 left+right union 模拟 |
| 自关联 | 同表 join 两次（a/b 别名） | 用于"相互关注""日期衔接" |
| 非等值 join | 条件是 `<`/`>` 等而非 `=` | 会数据放大，注意行数 |

## 易错点

- **NOT IN + NULL 陷阱**（面试高频）：子查询结果集含 NULL 时 `NOT IN` 整体返回空。规避：`NOT EXISTS` 或子查询加 `WHERE col IS NOT NULL`。
- 全称量词别只 `having count(*) >= N`，要验证"不满足条件的行不存在"。
""",
    ),
    Category(
        id="07",
        name="留存计算 / Retention Calculation",
        db_file="07_retention.db",
        order=7,
        problems=[
            Problem(
                id="07_01",
                category_id="07",
                title="七日留存计算",
                difficulty=3,
                tags=["留存", "retention", "left join"],
                description="""
给定用户每日活跃表，计算七日留存率（Day0 活跃的用户在 Day7 仍然活跃的比例）。

English: Given daily user activity, calculate the 7-day retention rate: the proportion of Day 0 users who are still active on Day 7. Use MIN date + LEFT JOIN to Day 7 records.
""",
                reference_sql="""
SELECT a.first_date,
       COUNT(DISTINCT a.user_id) AS day0_users,
       COUNT(DISTINCT b.user_id) AS day7_users,
       ROUND(COUNT(DISTINCT b.user_id) * 100.0 / COUNT(DISTINCT a.user_id), 2) AS retention_pct
FROM (
    SELECT user_id, MIN(date) AS first_date
    FROM user_active
    GROUP BY user_id
) a
LEFT JOIN user_active b
  ON a.user_id = b.user_id AND b.date = DATE_ADD(a.first_date, INTERVAL 7 DAY)
GROUP BY a.first_date;
""",
                tables=["user_active"],
                hints=[
                    "先找每个用户的首次活跃日期",
                    "再 left join 7 天后的活跃记录",
                    "计算比例"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **N 日留存套路**：`min(date)` 定首活 → `left join` 第 N 天活跃 → `count(distinct)` 分子分母。先给每个用户打上首活日标签，再回头找他第 N 天是否出现。
- **窗口法（可选替代）**：不必自关联 `min(date)`——先 `MIN(date) OVER (PARTITION BY user_id)` 给每行打上首活日列，再对 `date = DATE_ADD(首活日, INTERVAL N DAY)` 的行 `count(distinct)` 做分子；少一层 join，逻辑等价。
- **首日定义口径**：先问清是"首活"（min(活跃日期)，本题口径）还是"注册"（单独的注册表/注册日）；口径不同分母完全不同，面试先确认口径再写 SQL 是加分项。
- **多日留存公式展开**：次日/7 日/30 日留存同一套骨架，只换 INTERVAL——`left join b ON b.uid = a.uid AND b.date = a.首活日 + N 天`，`留存率 = count(distinct b.uid) / count(distinct a.uid)`；多天批量出结果时可对活跃表按 `DATEDIFF(date, 首活日)` 打 day_n 标签，一次 group by 首活日 + day_n 全出。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `left join` | 保左表全量，右表缺失补 NULL | 保分母不丢（留存题关键） |
| `count(distinct uid)` | 去重计数 | 留存分子分母都要去重 |
| `date_add(首活日, N)` | 首活日加 N 天 | 与活跃日期精确匹配即次日/7日留存 |
| `MIN(date) OVER (PARTITION BY uid)` | 每行附首活日列 | 窗口法核心，免自关联 |
| `DATEDIFF(date, 首活日)` | 距首活天数 | 打 day_n 标签，批量出多日留存 |

窗口法留存骨架（备查）：

```sql
SELECT first_date,
       COUNT(DISTINCT user_id) AS day0_users,
       COUNT(DISTINCT CASE WHEN date = DATE_ADD(first_date, INTERVAL 7 DAY)
                           THEN user_id END) AS day7_users
FROM (
    SELECT user_id, date,
           MIN(date) OVER (PARTITION BY user_id) AS first_date
    FROM user_active
) t
GROUP BY first_date;
```

多日留存批量口径：对每行打 `day_n = DATEDIFF(date, first_date)`，再 `GROUP BY first_date, day_n` 透视出 day1/day7/day30 各列，避免逐个 INTERVAL 重复 join N 次。

## 易错点

- 分母必须用 `left join` 不能用 `inner join`：inner join 会把没回流的新用户整行丢掉，留存率虚高。
- 首活日要作为派生列先固化（子查询/CTE），不要在 join 条件里重复计算导致逻辑混乱。
- "精确等于第 N 天"与"N 天内活跃过"是两种口径（经典 vs 宽口径），题目没说清时先确认。
""",
    ),
    Category(
        id="08",
        name="数据展开与收缩 / Data Expansion & Contraction",
        db_file="08_expand_contract.db",
        order=8,
        problems=[
            Problem(
                id="08_01",
                category_id="08",
                title="数据展开",
                difficulty=2,
                tags=["展开", "行转列"],
                description="""
给定一个用户和其标签列表（逗号分隔），把标签展开为多行。

English: Given users with comma-separated tags, expand each tag into its own row (string-to-rows). Use recursive CTE in MySQL 8 to simulate explode.
""",
                reference_sql="""
-- MySQL 8 用递归 CTE 模拟 explode（对应 Hive 的 lateral view explode）
-- CAST 锚定列宽，避免递归部分 SUBSTR 结果被截断
WITH RECURSIVE split(user_id, tag, rest) AS (
    SELECT user_id, CAST('' AS CHAR(128)), CONCAT(tags, ',')
    FROM user_tags
    UNION ALL
    SELECT user_id,
           SUBSTR(rest, 1, INSTR(rest, ',') - 1),
           SUBSTR(rest, INSTR(rest, ',') + 1)
    FROM split
    WHERE rest != ''
)
SELECT user_id, tag FROM split WHERE tag != '';
""",
                tables=["user_tags"],
                hints=[
                    "用 recursive CTE 模拟 explode",
                    "逐字符解析逗号分隔的字符串"
                ],
            ),
            Problem(
                id="08_02",
                category_id="08",
                title="数据收缩（合并）",
                difficulty=2,
                tags=["收缩", "列转行", "group_concat"],
                description="""
把多行数据按用户合并为一行（聚合标签）。

English: Aggregate multiple rows per user back into a single row with concatenated tags (rows-to-string). Use GROUP_CONCAT in MySQL 8.
""",
                reference_sql="""
SELECT user_id,
       GROUP_CONCAT(tag SEPARATOR ',') AS tags
FROM user_tag_rows
GROUP BY user_id;
""",
                tables=["user_tag_rows"],
                hints=["MySQL 用 GROUP_CONCAT(col SEPARATOR ',') 做字符串聚合"],
            ),
        ],
        knowledge="""## 解题思路

- **行转列（展开）**：见 05 系炸裂函数——Hive `lateral view explode(split(col, ','))`；MySQL 8 `JSON_TABLE` / 递归 CTE。
- **列转行（收缩，多行并一行）**：MySQL 8 用 `GROUP_CONCAT(col SEPARATOR ',')`；Hive 用 `concat_ws(',', collect_list(col))`。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `GROUP_CONCAT(col SEPARATOR ',')` | 组内多行拼成一个字符串 | MySQL 8；默认逗号，可自定义 SEPARATOR |
| `concat_ws(',', col...)` | 用指定分隔符拼接，跳过 NULL | Hive/MySQL 通用 |
| `collect_list(col)` | 组内聚合为数组，保留重复 | Hive |
| `collect_set(col)` | 组内聚合为数组，去重 | 与 collect_list 相对 |

GROUP_CONCAT 完整语法示例（含组内排序与去重）：

```sql
SELECT user_id,
       GROUP_CONCAT(DISTINCT tag ORDER BY tag SEPARATOR ',') AS tags
FROM user_tag_rows
GROUP BY user_id;
```

行转列 / 列转行对照示例表：

| 原始（多行） | 展开方向 | 结果 |
|---|---|---|
| (u1, 'a') (u1, 'b') (u1, 'c') | 收缩（GROUP_CONCAT） | (u1, 'a,b,c') |
| (u1, 'a,b,c') | 展开（explode/递归 CTE） | (u1, 'a') (u1, 'b') (u1, 'c') |

## 易错点

- `GROUP_CONCAT` 默认有长度上限（`group_concat_max_len`），长结果会被截断。
- `concat_ws` 跳过 NULL 但 `concat` 遇 NULL 返回 NULL——拼接用户数据优先 `concat_ws`。
- `GROUP_CONCAT` 组内顺序不保证，要稳定输出必须显式 `ORDER BY`。
""",
    ),
    Category(
        id="09",
        name="合并区间 / Merge Intervals",
        db_file="09_merge_interval.db",
        order=9,
        problems=[
            Problem(
                id="09_01",
                category_id="09",
                title="状态标记",
                difficulty=2,
                tags=["状态", "标记"],
                description="""
给定状态变更日志，标记每个时间段的状态。

English: Given a status change log, mark each time period with its corresponding status. Use LEAD to get the next timestamp as the current status end time.
""",
                reference_sql="""
SELECT id, status, start_time,
       LEAD(start_time) OVER (PARTITION BY id ORDER BY start_time) AS end_time
FROM status_log;
""",
                tables=["status_log"],
                hints=["lead 取下一行时间作为当前状态的结束时间"],
            ),
            Problem(
                id="09_02",
                category_id="09",
                title="填补缺失值",
                difficulty=3,
                tags=["缺失值", "lag", "填充"],
                description="""
用上一个非空值填充缺失值（forward fill）。

English: Forward-fill missing (NULL) values with the most recent non-null value. Use a correlated subquery or recursive CTE.
""",
                reference_sql="""
-- 用子查询 + lag 技术填充
WITH filled AS (
    SELECT id, date, value,
           CASE WHEN value IS NOT NULL THEN value
                ELSE (SELECT t2.value FROM sparse_readings t2
                      WHERE t2.id = t1.id AND t2.date < t1.date AND t2.value IS NOT NULL
                      ORDER BY t2.date DESC LIMIT 1)
           END AS filled_value
    FROM sparse_readings t1
)
SELECT * FROM filled;
""",
                tables=["sparse_readings"],
                hints=["用子查询查最近的非空值", "或递归 CTE 逐行填充"],
            ),
        ],
        knowledge="""## 解题思路

- **区间断点分段**：`lag(end)` 与当前 `start` 比较 → `case` 造 0/1 断点标志 → `sum() over` 累加成组号 → `min(start), max(end)` 按组合并。
- **状态标记**：`lead` 取下一行时间作为当前状态的结束时间——把状态变化流转成 [开始, 结束) 区间。
- **缺失值填充**：相关子查询取"最近的非空前值"（forward fill）；也可用 `last_value` 配显式帧。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `lag(col) over(order by ...)` | 取前一行区间端点 | 区间断点比较的核心 |
| `case when ... then 1 else 0 end` | 造断点标志 | 与 sum() over 累加配合 |
| `sum(标志) over(order by ...)` | 标志累加 = 分段组号 | SUM 标志累加分段法 |
| `lead(col) over(order by ...)` | 取下一行作为当前行区间结束 | 状态流转题常用 |

## 易错点

- 断点方向别搞反：`start > lag(end)` 说明出现间隙，要开新组；相等仍是同组。
- `sum` 累加分段时 ORDER BY 必须与业务时间序一致，乱序会导致组号错乱。
""",
    ),
    Category(
        id="10",
        name="人事数仓表格设计 / HR Data Warehouse Design",
        db_file="10_hr_warehouse.db",
        order=10,
        problems=[
            Problem(
                id="10_01",
                category_id="10",
                title="看似递归实则开窗误导题型",
                difficulty=4,
                tags=["递归", "开窗", "误导"],
                description="""
一些看似需要递归但实际可以用开窗函数解决的题目。典型场景：计算连续值、层级汇总等。

English: Problems that appear to require recursive CTEs but can actually be solved more elegantly with window functions. Typical scenarios: consecutive values, hierarchical summaries.
""",
                reference_sql="""
-- 示例：计算树形结构中的节点深度（以为要递归，实则可用路径排序）
-- 用 row_number + 层级前缀实现
""",
                tables=[],
                hints=["先想开窗函数能不能解决，不行再用递归"],
            ),
            Problem(
                id="10_02",
                category_id="10",
                title="人事数仓表格设计",
                difficulty=3,
                tags=["数仓", "表格设计", "人事"],
                description="""
设计人事数仓核心表结构：员工表、部门表、薪资表、考勤表。

English: Design core HR data warehouse tables: employee dimension, department, salary fact, attendance fact. Follow star/snowflake schema best practices.
""",
                reference_sql="""
-- 员工表
CREATE TABLE employee (
    emp_id INT PRIMARY KEY,
    name VARCHAR(128),
    dept_id INT,
    hire_date VARCHAR(10),
    status VARCHAR(128)
);

-- 薪资表
CREATE TABLE salary (
    emp_id INT,
    month VARCHAR(7),
    base_salary DOUBLE,
    bonus DOUBLE,
    PRIMARY KEY (emp_id, month)
);

-- 考勤表
CREATE TABLE attendance (
    emp_id INT,
    date VARCHAR(10),
    check_in VARCHAR(20),
    check_out VARCHAR(20)
);
""",
                tables=["employee", "salary", "attendance"],
                hints=["标准数仓建模：事实表 + 维度表", "星型/雪花模型"],
            ),
        ],
        knowledge="""## 解题思路

- **建模题先答架构**：星型/雪花建模——事实表 + 维度表。员工是维度（employee），薪资、考勤是事实（salary/attendance 事实表）。
- **递归 vs 开窗辨析**：先看能否用 `row_number/lag` + 聚合开窗的"分段子问题"套路解决（连续、分段、层级汇总大多可以）；真需要逐行传递状态（逐行 forward fill、树遍历）才用递归。面试先答开窗解法是加分项。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| 事实表 | 记录业务事件（可加、量大），外键指向维度 | 如薪资/考勤流水 |
| 维度表 | 描述实体属性（如员工、部门） | 主键被事实表引用 |
| 星型模型 | 维度表不拆分，事实表居中 | 查询少 join，数仓首选 |
| 雪花模型 | 维度表继续拆分规范化 | 省 space 但 join 多 |
| 缓慢变化维（SCD） | 维度属性随时间变化，用拉链表/版本号保留历史 | 一句话：保历史用拉链 |
| `WITH RECURSIVE` | 逐行传递状态 / 树遍历 | 开窗解决不了再上 |

## 易错点

- 设计题不是纯 SQL 题：先讲分层（ODS/DWD/DWS）与模型，再落表结构，别上来就写建表语句。
- 递归 CTE 要有终止条件（层级上限/状态收敛），否则死循环。
""",
    ),
    Category(
        id="11",
        name="日期处理 / Date Processing",
        db_file="11_date_processing.db",
        order=11,
        problems=[
            Problem(
                id="11_01",
                category_id="11",
                title="日期处理系列 — year 格式",
                difficulty=2,
                tags=["日期", "year", "格式化"],
                description="""
将日期转换为 yyyy 格式。

English: Convert date strings to yyyy format using SUBSTR.
""",
                reference_sql="""
SELECT date, SUBSTR(date, 1, 4) AS year
FROM raw_dates;
""",
                tables=["raw_dates"],
                hints=["标准日期用 strftime('%Y', date) 更通用"],
            ),
            Problem(
                id="11_02",
                category_id="11",
                title="日期处理 — quarter 格式",
                difficulty=2,
                tags=["日期", "季度"],
                description="""
将日期转换为 yyyyQn 格式（季度）。

English: Convert date strings to yyyyQn (quarter) format. Formula: (month-1)//3 + 1.
""",
                reference_sql="""
SELECT date,
       CONCAT(SUBSTR(date, 1, 4), 'Q',
              (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 3 + 1) AS quarter
FROM raw_dates;
""",
                tables=["raw_dates"],
                hints=["公式: (month-1)//3 + 1 得到季度号"],
            ),
            Problem(
                id="11_03",
                category_id="11",
                title="日期处理 — 最终代码汇总",
                difficulty=2,
                tags=["日期", "汇总"],
                description="""
汇总所有日期格式转换的代码：year, mm, quarter, half, h2t1, ytm, last*系列。

English: Summary of all date format conversions: year, month, quarter, half-year, YYYYMM, last12m, last30d/60d/90d/180d.
""",
                reference_sql="""
-- year:  SUBSTR(date, 1, 4)
-- mm:    SUBSTR(date, 6, 2)
-- quarter: CONCAT(SUBSTR(date, 1, 4), 'Q', (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 3 + 1)
-- half:  CONCAT(SUBSTR(date, 1, 4), 'H', (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 6 + 1)
-- ytm:   日期转 YYYYMM 格式
-- last12m: 最近12个月（date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)）
-- last30d/60d/90d/180d: 类似，用 DATE_SUB
""",
                tables=["raw_dates"],
                hints=["记住 substr + 算术的组合模式"],
            ),
        ],
        knowledge="""## 解题思路

- 核心套路是 `substr` + 算术组合：字符串截取拿年月，整数除法换算季度/半年。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `substr(date, 1, 4)` | 取年 | year |
| `substr(date, 6, 2)` | 取月 | mm |
| `(month-1) DIV 3 + 1` | 季度公式 | 配 `concat(substr(date,1,4),'Q',...)` 拼出 2024Q1 |
| `(m-1) DIV 6 + 1` | 半年公式 | H1/H2 |
| `substr(date, 1, 7)` | 取年月 | ytm |
| `date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)` | last12m 滚动窗口 | last30d/60d/90d/180d 同理换 INTERVAL |
| `last_day(d)` | 取月末 | 滚动窗口常用 |

## 易错点

- Hive 整除用 `div`（`/` 恒返回 double），MySQL 整除用 `DIV`——季度公式照抄要换方言。
- Hive 的 `date_add(d, n)` 不是 `INTERVAL` 语法；MySQL 才写 `DATE_SUB(d, INTERVAL n DAY)`。
""",
    ),
    Category(
        id="12",
        name="大厂原题 / Big Tech Interview Questions",
        db_file="12_company_questions.db",
        order=12,
        problems=[
            Problem(
                id="12_01",
                category_id="12",
                title="字节 — 题1",
                difficulty=3,
                tags=["字节", "大厂", "stub"],
                description="字节跳动面试原题。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
            Problem(
                id="12_02",
                category_id="12",
                title="字节 — 题2",
                difficulty=3,
                tags=["字节", "大厂", "stub"],
                description="字节跳动面试原题。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
            Problem(
                id="12_03",
                category_id="12",
                title="得物实际场景需求",
                difficulty=4,
                tags=["得物", "大厂", "场景", "stub"],
                description="得物真实业务场景 SQL 需求。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
            Problem(
                id="12_04",
                category_id="12",
                title="阿里面试题",
                difficulty=4,
                tags=["阿里", "大厂", "stub"],
                description="阿里巴巴面试原题。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
            Problem(
                id="12_05",
                category_id="12",
                title="拼多多面试题",
                difficulty=3,
                tags=["拼多多", "大厂", "stub"],
                description="拼多多面试原题。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
        ],
        knowledge="""## 解题思路

- 本专题题目持续补充中（题目在题目描述里给出），先背下面这份**面试通用追问清单**，任何大厂原题都能挂靠。

## 必背知识点

| 追问 | 口诀 | 备注 |
|---|---|---|
| 窗口函数 vs GROUP BY | GROUP BY 压缩为每组一行；窗口函数保留每行、附加计算列 | 要"既有明细又有聚合"只能用窗口 |
| COUNT(DISTINCT) 数据倾斜 | 先 `group by` 预聚合打散 / 两阶段 distinct | 单 reducer 聚合大维度是倾斜根源 |
| 千亿级 join 优化 | 小表广播 mapjoin / 分桶 bucket join / Bloom filter 预过滤 | 避免非等值 join 的笛卡尔放大 |
| union all vs union | union all 保留全部（含重复）；union 去重触发 shuffle 代价高 | 进出场计数必须用 union all |

追问话术示例（每条追问的标准回答方向，照这个结构展开）：

- 被问"窗口函数 vs GROUP BY，什么时候必须用窗口"→ 回答方向：要"明细行 + 聚合列"并存（如累计、环比、组内排名）时只能用窗口；GROUP BY 会把明细压掉，举 sum() over 累计一例即可。
- 被问"COUNT(DISTINCT) 为什么慢，怎么优化"→ 回答方向：成因是 distinct key 分布不均、单 reducer 聚合长尾；方案：先按弱维度 group by 预聚合打散，或两阶段 distinct（先组内去重再全局去重）。
- 被问"千亿级 join 怎么优化"→ 回答方向：小表广播 mapjoin、分桶 bucket join 让同 key 数据同节点、Bloom filter 预过滤；核心都是避免全量 shuffle join。
- 被问"union all 和 union 差在哪"→ 回答方向：union 去重要触发一次 shuffle + 去重代价，union all 直接拼接；能用 union all 的场景（如进出场 +1/-1 计数）绝不用 union。

追问回答的通用三步结构（背下来套任何追问）：① 先复述问题成因（一句话定性）；② 给 2 个以上方案并点明各自适用场景/代价；③ 落到本题数据规模给一个推荐方案——展示"知道为什么"而不只是"知道怎么办"。

完整示范（以数据倾斜为例）：

> "这个慢的根因是某个 distinct key（如热门商品）占了大量行，聚合时全落到同一个 reducer 形成长尾。方案一是先按 user_id 等弱维度 group by 预聚合打散，方案二是两阶段 distinct。本题维度假定基数在千万级，我推荐方案一，代价是多一轮 job 但长尾消除。"

## 易错点

- 追问回答要给"问题成因 + 两个以上方案"，只报函数名拿不到加分。
- 数据倾斜先说"key 分布不均 → 单 reducer 长尾"，再说打散方案，逻辑链完整。
""",
    ),
    Category(
        id="13",
        name="JSON 解析 / JSON Parsing",
        db_file="13_json_parsing.db",
        order=13,
        problems=[
            Problem(
                id="13_01",
                category_id="13",
                title="JSON 解析系列",
                difficulty=3,
                tags=["json", "解析"],
                description="""
MySQL 8 中解析 JSON 字段的方法（JSON_EXTRACT 提取字段，JSON_TABLE 展开数组）。

English: Parse JSON fields in MySQL 8: JSON_EXTRACT() to access keys, JSON_TABLE() to expand arrays (the MySQL counterpart of Hive's explode).
""",
                reference_sql="""
-- MySQL 8 内置 JSON 函数
SELECT id,
       JSON_EXTRACT(data, '$.name') AS name,
       JSON_EXTRACT(data, '$.age') AS age
FROM user_profiles;

-- 展开 JSON 数组（JSON_TABLE 是 MySQL 8 表函数，对应 Hive 的 lateral view explode）
SELECT jt.id,
       items.item
FROM user_profiles jt,
     JSON_TABLE(jt.data, '$.items[*]'
         COLUMNS (item VARCHAR(64) PATH '$')) AS items;
""",
                tables=["user_profiles"],
                hints=[
                    "JSON_EXTRACT(col, '$.key') 提取字段",
                    "JSON_TABLE(col, '$.array[*]' COLUMNS (...)) 展开数组"
                ],
            ),
        ],
        knowledge="""## 解题思路

- **字段提取**：MySQL 8 用 `JSON_EXTRACT(col, '$.key')` 取 JSON 字段值。
- **数组展开**：`JSON_TABLE` 把 JSON 数组炸成多行——对应 Hive 的 `lateral view explode`。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `JSON_EXTRACT(col, '$.key')` | 按 JSON 路径取值 | 路径语法 `'$.key'` |
| `JSON_TABLE(col, '$.items[*]' COLUMNS (item VARCHAR(64) PATH '$'))` | 表函数：JSON 数组展开为行 | 语法骨架必背 |
| JSON_TABLE 连用 | 是 MySQL 8 表函数，与主表**逗号**连用 | `FROM t, JSON_TABLE(...)` |
| `JSON_UNQUOTE(JSON_EXTRACT(col, '$.key'))` | 去掉返回值的 JSON 引号，得纯文本 | 等价简写 `col->>'$.key'` |
| `col->>'$.key'` | 提取 + 去引号一步到位（`->` 则仍带引号） | 结果可直接 `=` 字符串比较 |

JSON_EXTRACT 返回类型注意：返回的是 **JSON 类型值**，字符串会带引号——`JSON_EXTRACT('{"a":"x"}', '$.a')` 得到 `"x"`（含双引号），与 `'x'` 比较永远不等；要文本必须 `JSON_UNQUOTE` 或用 `->>`。

JSON_UNQUOTE 与 `->>` 用法示例：

```sql
SELECT id,
       data->>'$.name'                         AS name,        -- 推荐：去引号
       JSON_UNQUOTE(JSON_EXTRACT(data, '$.name')) AS name_same  -- 等价长写法
FROM user_profiles
WHERE data->>'$.name' = 'alice';               -- 用 ->> 才能匹配上
```

JSON_TABLE 展开多字段（数组元素是对象时，COLUMNS 里逐字段声明 PATH）：

```sql
SELECT jt.id, ord.order_id, ord.amount
FROM user_profiles jt,
     JSON_TABLE(jt.data, '$.orders[*]'
         COLUMNS (order_id VARCHAR(32) PATH '$.order_id',
                  amount      DECIMAL(10,2) PATH '$.amount')) AS ord;
```

## 易错点

- 表名不要撞 MySQL 保留函数名（早期示例表名叫 json_table 会报语法错误，本题已改用 user_profiles）。
- `JSON_EXTRACT` 返回带引号的 JSON 值，要文本需再套 `JSON_UNQUOTE` 或 `->>'$.key'`。
- `->` 与 `->>` 一字之差：`->` 等价 JSON_EXTRACT（带引号），`->>` 才是提取 + 去引号。
""",
    ),
    Category(
        id="14",
        name="趣味 SQL / Fun SQL",
        db_file="14_fun_sql.db",
        order=14,
        problems=[
            Problem(
                id="14_01",
                category_id="14",
                title="接雨水问题",
                difficulty=5,
                tags=["趣味", "算法", "接雨水"],
                description="""
如何用 SQL 求解经典算法题「接雨水」？（给定柱子高度数组，计算能接多少雨水）

English: Solve the classic "Trapping Rain Water" algorithm problem in SQL. For each position, water = min(left_max, right_max) - height. Use MAX() over() for rolling maxima.
""",
                reference_sql="""
WITH left_max AS (
    SELECT idx, height,
           MAX(height) OVER (ORDER BY idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS lmax
    FROM heights
),
right_max AS (
    SELECT idx, height, lmax,
           MAX(height) OVER (ORDER BY idx DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rmax
    FROM left_max
)
SELECT SUM(LEAST(lmax, rmax) - height) AS total_water
FROM right_max
WHERE LEAST(lmax, rmax) > height;
""",
                tables=["heights"],
                hints=[
                    "每个位置的储水量 = min(左边最高, 右边最高) - 当前高度",
                    "用 max() over(order by) 分别计算左右两边的滚动最大值"
                ],
            ),
            Problem(
                id="14_02",
                category_id="14",
                title="墨天轮 SQL 挑战赛第二期",
                difficulty=4,
                tags=["挑战赛", "趣味", "stub"],
                description="墨天轮 SQL 挑战赛题目。",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
            Problem(
                id="14_03",
                category_id="14",
                title="赛马问题",
                difficulty=4,
                tags=["趣味", "赛马", "非等值关联"],
                description="""
如何用 SQL 解决趣味赛马问题（非等值关联匹配）？

English: Solve the horse racing problem using non-equi joins: for each horse, find the next faster horse using a correlated subquery.
""",
                reference_sql="""
-- 非等值关联：找每匹马比自己快的前一匹
SELECT a.horse, a.time,
       b.horse AS faster_horse
FROM race_result a
LEFT JOIN race_result b ON b.time < a.time
WHERE b.time = (SELECT MIN(time) FROM race_result WHERE time < a.time);
""",
                tables=["race_result"],
                hints=["非等值 JOIN 模拟排序", "子查询取前一个值"],
            ),
            Problem(
                id="14_04",
                category_id="14",
                title="块熵计算",
                difficulty=5,
                tags=["熵", "趣味", "信息论", "stub"],
                description="如何用 SQL 计算块熵（Block Entropy）？",
                reference_sql="-- 待补充",
                tables=[],
                hints=["题目内容待从原始文档补充"],
            ),
        ],
        knowledge="""## 解题思路

- **接雨水**：每位储水 = `least(左滚动max, 右滚动max) - 当前高`，两侧 `max() over` 求出——正序扫一遍取左侧最高，倒序扫一遍取右侧最高。注意右滚动 max 没有单独的"向后看"语法，需按时间倒序排列的窗口（`ORDER BY idx DESC`）实现。
- **找相邻更快者**：非等值 join `b.time < a.time` + 取 `min`；更优解：`lag() over(order by time)` 一次扫描完成。

## 必背知识点

| 函数/语法 | 语义 | 备注 |
|---|---|---|
| `max() over(order by ...)` | 滚动极值（到当前行为止的最大/最小） | 接雨水左右两侧最高墙 |
| `least(a, b)` / `greatest(a, b)` | 多参取小/取大 | 左右 min 再减当前高 |
| 非等值 join | `b.time < a.time` 之类条件 join | 会数据放大，注意行数 |
| `lag() over(order by time)` | 取排序后的前一行 | 相邻比较优于 join 的原因 |

## 易错点

- 接雨水负值要过滤：两端位置储水为 0（`least - 高` 可能算出负数，外层套 `greatest(..., 0)` 或 case 过滤）。
- 非等值 join 是 O(n²) 放大，数据大优先想 `lag` 单遍扫描方案。
""",
    ),
]


# ============================================================
# 辅助函数
# ============================================================

def get_all_problems() -> List[Problem]:
    """获取所有题目列表（扁平化）"""
    result = []
    for cat in CATEGORIES:
        result.extend(cat.problems)
    return result


def get_category(category_id: str) -> Optional[Category]:
    for cat in CATEGORIES:
        if cat.id == category_id:
            return cat
    return None


def get_problem(problem_id: str) -> Optional[Problem]:
    for prob in get_all_problems():
        if prob.id == problem_id:
            return prob
    return None
