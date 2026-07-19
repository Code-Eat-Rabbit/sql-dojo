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


@dataclass
class Category:
    """一个 SQL 练习专题，包含一组相关题目。

    Attributes:
        id: 专题唯一标识，如 "01"。
        name: 专题名称，如 "连续登陆"。
        db_file: 对应的 SQLite 数据库文件名。
        order: 排序序号。
        problems: 该专题包含的题目列表。
    """
    id: str
    name: str
    db_file: str           # "01_continuous_login.db"
    order: int
    problems: List[Problem]


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
给定一张用户登录表 `test`，包含字段 `id`（用户ID）和 `date`（登录日期）。
请查询连续登录 3 天以上的所有用户。

**补充知识点：** 字段名相同不会覆盖，例如 `select a,a,a` 结果有三列。

English: Given a user login table `test` with fields `id` (user ID) and `date` (login date), find all users who logged in for 3 or more consecutive days.
""",
                reference_sql="""
-- 步骤一：去重
SELECT id, substr(date, 1, 10) AS date
FROM test
GROUP BY id, substr(date, 1, 10);

-- 步骤二：用 row_number 标记分组
SELECT id, date,
       date_add(date, -ROW_NUMBER() OVER (PARTITION BY id ORDER BY date)) AS date1
FROM (步骤一);

-- 步骤三：统计连续天数
SELECT id, date1, COUNT(*) AS day_cnt
FROM (步骤二)
GROUP BY id, date1
HAVING COUNT(*) > 3;
""",
                tables=["test"],
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
承接上一题，查询每个用户连续登录的最大天数。

English: Following the previous problem, find the maximum consecutive login days for each user.
""",
                reference_sql="""
-- 承接上一问第二步
-- select id, date1, count(*) as day_cnt from (第二步子查询) group by id, date

-- 最终：
SELECT id, MAX(day_cnt) AS max_day_cnt
FROM (第三步子查询)
GROUP BY id;
""",
                tables=["test"],
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
用三种不同方法实现「查询连续登录 3 天以上的用户」：
1. row_number() 法
2. lag/lead 法  
3. 自关联法

English: Solve "users who logged in 3+ consecutive days" using three different methods:
1. row_number() method
2. lag/lead method
3. Self-join method
""",
                reference_sql="""
-- 方法1: row_number()
-- （同 01_01）

-- 方法2: lag()
SELECT DISTINCT id
FROM (
    SELECT id, date,
           LAG(date, 1) OVER (PARTITION BY id ORDER BY date) AS prev1,
           LAG(date, 2) OVER (PARTITION BY id ORDER BY date) AS prev2
    FROM (SELECT id, substr(date,1,10) AS date FROM test GROUP BY id, substr(date,1,10))
) t
WHERE DATEDIFF(date, prev1) = 1 AND DATEDIFF(prev1, prev2) = 1;

-- 方法3: 自关联
SELECT DISTINCT a.id
FROM (SELECT id, substr(date,1,10) AS date FROM test GROUP BY id, substr(date,1,10)) a
JOIN (SELECT id, substr(date,1,10) AS date FROM test GROUP BY id, substr(date,1,10)) b
  ON a.id = b.id AND DATEDIFF(a.date, b.date) = 1
JOIN (SELECT id, substr(date,1,10) AS date FROM test GROUP BY id, substr(date,1,10)) c
  ON b.id = c.id AND DATEDIFF(b.date, c.date) = 1;
""",
                tables=["test"],
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
总结连续类 SQL 题的核心思路。

English: Summary: The core approach for consecutive-type SQL problems. Use `row_number() over()` to create a grouping key, then group and count.
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
某外汇公司面试题：给定用户账户表，查询账户余额大于 1000 的连续天数。

English: Given a forex company's account table, find consecutive days where the account balance exceeds 1000. Filter first, then apply the consecutive-days pattern.
""",
                reference_sql="""
-- 先筛选余额 > 1000 的行，再套用连续类题的思路
WITH filtered AS (
    SELECT user_id, date, balance
    FROM account
    WHERE balance > 1000
)
SELECT user_id,
       date_sub(date, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date)) AS grp,
       COUNT(*) AS consecutive_days
FROM filtered
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
给定一组日期区间（start_date, end_date），合并连续或重叠的区间。

English: Given a set of date intervals (start_date, end_date), merge consecutive or overlapping intervals. Use lag to detect gaps, then sum flags to create group IDs.
""",
                reference_sql="""
WITH t1 AS (
    SELECT id, NAME, start_date, end_date,
           LAG(end_date) OVER (PARTITION BY id, NAME ORDER BY start_date) AS lag_date,
           CASE
               WHEN DATE_ADD(LAG(end_date) OVER (PARTITION BY id, NAME ORDER BY start_date), INTERVAL 1 DAY) = start_date
               THEN 0 ELSE 1
           END AS new_group_flag
    FROM mydb.test_xiaoming
),
t2 AS (
    SELECT id, NAME, start_date, end_date,
           SUM(new_group_flag) OVER (PARTITION BY id, NAME ORDER BY start_date) AS group_id
    FROM t1
)
SELECT id, NAME,
       MIN(start_date) AS start_date,
       MAX(end_date) AS end_date
FROM t2
GROUP BY id, NAME, group_id
ORDER BY MIN(start_date), id, NAME;
""",
                tables=["test_xiaoming"],
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
计算每个用户的连胜数（最长连续胜场）。

English: Calculate each user's longest winning streak. Isolate "win" rows, then use the row_number difference trick to group consecutive wins.
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
)
SELECT user_id,
       SUM(new_streak) OVER (PARTITION BY user_id ORDER BY date) AS streak_id,
       COUNT(*) AS streak_len
FROM marked
WHERE result = 'win'
GROUP BY user_id, streak_id;
""",
                tables=["games"],
                hints=[
                    "连续类题的变体：把'连续'条件从日期改为胜负状态",
                    "关键：把 win 的行单独拎出来，然后用 row_number 差值法"
                ],
            ),
        ],
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
给定股票/商品价格时间序列表，标记每个时间点是「波峰」还是「波谷」。
波峰：价格大于前一天和后一天；波谷反之。

English: Given a stock/commodity price time series, mark each time point as "peak" (price > previous and next) or "trough" (price < previous and next). Use LAG and LEAD window functions.
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
把前一行和后一行的数据放到当前行，作为新列展示。

English: Move the previous row's value and the next row's value into the current row as new columns using LAG and LEAD.
""",
                reference_sql="""
SELECT id, date, value,
       LAG(value) OVER (PARTITION BY id ORDER BY date) AS prev_value,
       LEAD(value) OVER (PARTITION BY id ORDER BY date) AS next_value
FROM data_table;
""",
                tables=["data_table"],
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
真实面试题（lag/lead 综合应用）。

English: A real interview question covering comprehensive LAG/LEAD usage, e.g., calculating period-over-period change rates.
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
掌握三种排序开窗函数的区别：
- `row_number()`: 连续编号 1,2,3,4...（不并列）
- `rank()`: 跳号 1,2,2,4...（并列同号，下一个跳号）
- `dense_rank()`: 不跳号 1,2,2,3...（并列同号，下一个不跳）

English: Master the three ranking window functions:
- `row_number()`: sequential 1,2,3,4... (no ties)
- `rank()`: gapped 1,2,2,4... (ties share rank, next skips)
- `dense_rank()`: gapless 1,2,2,3... (ties share rank, next does not skip)
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
给定学生成绩表（student, subject, score），查询每个学生成绩第二高的科目。

English: Given a student scores table (student, subject, score), find each student's second-highest scoring subject. Use DENSE_RANK with PARTITION BY.
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
用聚合开窗函数 `sum() over()` 统计每个用户按月累计访问次数。

English: Use `sum() over()` to calculate each user's cumulative visit count by month.
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
给定用户进入和离开直播间的时间，计算同时在线人数峰值。
核心技巧：进入 +1，离开 -1，按时间排序累加。

English: Peak concurrent online users: given user enter/leave timestamps, treat enter as +1 and leave as -1, then compute cumulative sum by time to find the maximum.
""",
                reference_sql="""
-- 步骤一：进入+1，离开-1
SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
WHERE substr(login_time, 1, 8) = '20210310'
UNION ALL
SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
WHERE substr(logout_time, 1, 8) = '20210310';

-- 步骤二：按时间累加
SELECT room_id, event_time,
       SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
FROM (步骤一);

-- 步骤三：取最大值
SELECT room_id, MAX(online_cnt) AS max_online
FROM (步骤二)
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
限定时段内，按每小时统计同时在线人数的最大值。

English: Within a specified time range, calculate the maximum concurrent online users per hour.
""",
                reference_sql="""
-- 在步骤二的 event_time 上加 substr 取小时粒度即可
SELECT room_id, substr(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (步骤一)
) t
GROUP BY room_id, substr(event_time, 1, 13);
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
不限制日期，统计有史以来每小时最大同时在线人数。

English: Remove the date filter to calculate all-time hourly maximum concurrent users.
""",
                reference_sql="""
-- 去掉 WHERE 日期筛选即可
SELECT room_id, substr(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (...去掉日期限制的子查询...) t
GROUP BY room_id, substr(event_time, 1, 13);
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
    WHERE substr(login_time, 1, 8) = '20220501'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE substr(logout_time, 1, 8) = '20220501'
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
           MIN(price) OVER (PARTITION BY id ORDER BY ds) AS min_price_so_far
    FROM product_price
)
SELECT id, ds, price
FROM min_so_far
WHERE price = min_price_so_far
  AND price < LAG(price) OVER (PARTITION BY id ORDER BY ds);
""",
                tables=["product_price"],
                hints=[
                    "min(price) over(partition by id order by ds) 实现滚动最小值",
                ],
            ),
        ],
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
groups AS (
    SELECT start, end, SUM(new_group) OVER (ORDER BY start) AS group_id
    FROM intervals
)
SELECT MIN(start) AS merged_start, MAX(end) AS merged_end
FROM groups
GROUP BY group_id;
""",
                tables=["raw_intervals"],
                hints=[
                    "用 max(end) over() 滚动获取之前的最大 end",
                    "start > 之前的 max_end 则开启新区间",
                ],
            ),
        ],
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

English: Given users with comma-separated tags, expand each tag into its own row (string-to-rows). Use recursive CTE in SQLite to simulate explode.
""",
                reference_sql="""
-- SQLite 中可以使用 recursive CTE 模拟 explode
WITH RECURSIVE split(user_id, tag, rest) AS (
    SELECT user_id, '', tags || ','
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

English: Aggregate multiple rows per user back into a single row with concatenated tags (rows-to-string). Use GROUP_CONCAT in SQLite.
""",
                reference_sql="""
SELECT user_id,
       GROUP_CONCAT(tag, ',') AS tags
FROM user_tag_rows
GROUP BY user_id;
""",
                tables=["user_tag_rows"],
                hints=["group_concat 是 SQLite 的字符串聚合函数"],
            ),
        ],
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
                ELSE (SELECT t2.value FROM data_table t2
                      WHERE t2.id = t1.id AND t2.date < t1.date AND t2.value IS NOT NULL
                      ORDER BY t2.date DESC LIMIT 1)
           END AS filled_value
    FROM data_table t1
)
SELECT * FROM filled;
""",
                tables=["data_table"],
                hints=["用子查询查最近的非空值", "或递归 CTE 逐行填充"],
            ),
        ],
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
    emp_id INTEGER PRIMARY KEY,
    name TEXT,
    dept_id INTEGER,
    hire_date TEXT,
    status TEXT
);

-- 薪资表
CREATE TABLE salary (
    emp_id INTEGER,
    month TEXT,
    base_salary REAL,
    bonus REAL,
    PRIMARY KEY (emp_id, month)
);

-- 考勤表
CREATE TABLE attendance (
    emp_id INTEGER,
    date TEXT,
    check_in TEXT,
    check_out TEXT
);
""",
                tables=["employee", "salary", "attendance"],
                hints=["标准数仓建模：事实表 + 维度表", "星型/雪花模型"],
            ),
        ],
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
FROM date_table;
""",
                tables=["date_table"],
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
       SUBSTR(date, 1, 4) || 'Q' || CAST((CAST(SUBSTR(date, 6, 2) AS INTEGER) - 1) / 3 + 1 AS TEXT) AS quarter
FROM date_table;
""",
                tables=["date_table"],
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
-- quarter: SUBSTR(date, 1, 4) || 'Q' || ((month-1)/3 + 1)
-- half:  SUBSTR(date, 1, 4) || 'H' || ((month-1)/6 + 1)
-- ytm:   日期转 YYYYMM 格式
-- last12m: 最近12个月（date >= date_sub(today, interval 12 month)）
-- last30d/60d/90d/180d: 类似，用 date_sub
""",
                tables=["date_table"],
                hints=["记住 substr + 算术的组合模式"],
            ),
        ],
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
SQLite 中解析 JSON 字段的方法（使用 json_extract 等内置函数）。

English: Parse JSON fields in SQLite using built-in functions: json_extract() to access keys, json_each() to expand arrays.
""",
                reference_sql="""
-- SQLite 内置 JSON 函数
SELECT id,
       JSON_EXTRACT(data, '$.name') AS name,
       JSON_EXTRACT(data, '$.age') AS age
FROM json_table;

-- 展开 JSON 数组
SELECT id,
       JSON_EACH.value AS item
FROM json_table, JSON_EACH(json_table.data, '$.items');
""",
                tables=["json_table"],
                hints=[
                    "json_extract(col, '$.key') 提取字段",
                    "json_each(col, '$.array') 展开数组"
                ],
            ),
        ],
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
WITH numbered AS (
    SELECT ROW_NUMBER() OVER () AS idx, height
    FROM heights
),
left_max AS (
    SELECT idx, height,
           MAX(height) OVER (ORDER BY idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS lmax
    FROM numbered
),
right_max AS (
    SELECT idx, height, lmax,
           MAX(height) OVER (ORDER BY idx DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rmax
    FROM left_max
)
SELECT SUM(MIN(lmax, rmax) - height) AS total_water
FROM right_max
WHERE MIN(lmax, rmax) > height;
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
