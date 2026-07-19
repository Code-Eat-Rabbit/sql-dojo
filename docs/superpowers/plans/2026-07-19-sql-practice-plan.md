# SQL 练习平台 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将「踏踏实实练SQL」文档（71 道 SQL 面试题）转化为可用的 SQL 练习平台——按专题分 SQLite 库 + FastAPI 后端 + React 前端 + 进度追踪。

**架构：** 14 个专题对应 14 个 SQLite 文件。Python data_builder 为每道题精准构造数据。FastAPI 读取 manifest 提供 REST API。React 两个页面展示题目和进度。用户通过 DBeaver 连接 SQLite 做 SQL 练习。

**技术栈：** Python 3.12 (sqlite3, faker, FastAPI, SQLAlchemy), React 18 (Vite, TypeScript, Tailwind CSS), SQLite

---

## 文件结构

```
sql_practice/
├── data_builder/
│   ├── manifest.py          # 专题/题目/表 元数据定义（单文件集中管理）
│   ├── generate.py          # 入口：遍历 manifest → 运行 builder → 输出 .db
│   ├── generate_data.py     # 数据生成入口：读取 manifest → 调用 builders → 输出 SQLite
│   └── builders/
│       ├── __init__.py
│       ├── 01_continuous_login.py
│       ├── 02_window_lead_lag.py
│       ├── 03_window_rank.py
│       ├── 04_cumulative_agg.py
│       ├── 05_explode.py
│       ├── 06_joins.py
│       ├── 07_retention.py
│       ├── 08_expand_contract.py
│       ├── 09_merge_interval.py
│       ├── 10_hr_warehouse.py
│       ├── 11_date_processing.py
│       ├── 12_company_questions.py
│       ├── 13_json_parsing.py
│       └── 14_fun_sql.py
├── backend/
│   ├── main.py              # FastAPI app 入口 + CORS + 静态文件挂载
│   ├── database.py          # progress.db 连接 + manifest 加载 + 多库 schema 读取
│   ├── models/
│   │   ├── __init__.py
│   │   ├── problem.py       # Problem, Progress Pydantic models
│   │   └── schemas.py       # API 响应/请求 schemas
│   └── routers/
│       ├── __init__.py
│       ├── categories.py    # GET /api/categories
│       ├── problems.py      # GET /api/problems, /api/problems/{id}, /api/problems/{id}/tables
│       ├── progress.py      # POST/PATCH /api/progress/{id}, GET /api/progress/summary
│       └── databases.py     # GET /api/databases/{id}/connect
├── frontend/                # React (Vite + TypeScript + Tailwind)
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts           # fetch 封装 + API 函数
│       ├── types.ts         # TypeScript 类型定义
│       ├── pages/
│       │   ├── CategoryListPage.tsx
│       │   └── ProblemListPage.tsx
│       └── components/
│           ├── GlobalProgressBar.tsx
│           ├── CategoryCard.tsx
│           ├── ProblemSidebar.tsx
│           ├── ProblemDetail.tsx
│           ├── TableSchema.tsx
│           ├── ReferenceAnswer.tsx
│           ├── ProgressPanel.tsx
│           ├── DbConnectionInfo.tsx
│           └── RatingModal.tsx
└── docs/
    └── superpowers/
        ├── specs/2026-07-19-sql-practice-design.md
        └── plans/2026-07-19-sql-practice-plan.md
```

---

### 任务 1：项目初始化

**文件：**
- 创建：`data_builder/__init__.py`（空）
- 创建：`.gitignore`

- [ ] **步骤 1：初始化 git + .gitignore**

```bash
cd /Users/yourton_ma/Documents/sql_practice
git init
```

- [ ] **步骤 2：创建 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/

# Databases
databases/*.db

# Frontend
frontend/node_modules/
frontend/dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

- [ ] **步骤 3：创建目录结构**

```bash
mkdir -p data_builder/builders
mkdir -p backend/models backend/routers
mkdir -p frontend/src/pages frontend/src/components
mkdir -p databases docs/superpowers/plans
touch data_builder/__init__.py data_builder/builders/__init__.py
touch backend/__init__.py backend/models/__init__.py backend/routers/__init__.py
```

- [ ] **步骤 4：Commit**

```bash
git add -A
git commit -m "chore: init project structure"
```

---

### 任务 2：manifest.py — 元数据定义

**文件：**
- 创建：`data_builder/manifest.py`

所有专题和题目的元数据集中在此文件。内容来源：spec 中定义的 manifest.json 结构 + 从文档提取的题目详情。

- [ ] **步骤 1：编写 manifest.py**

```python
"""SQL 练习平台 — 元数据定义

集中管理所有专题、题目、表的映射关系。
data_builder 用此生成数据库，backend 用此提供 API。
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Problem:
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
    id: str
    name: str
    db_file: str           # "01_continuous_login.db"
    order: int
    problems: List[Problem]


# ============================================================
# 专题定义
# ============================================================

CATEGORIES: List[Category] = [
    Category(
        id="01",
        name="连续登陆",
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
        name="开窗函数 lead/lag",
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
        name="三种排序开窗",
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
        name="累计汇总",
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
        name="炸裂函数",
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
        name="关联应用",
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
        name="留存计算",
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
        name="数据展开与收缩",
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
        name="合并区间",
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
        name="人事数仓表格设计",
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
        name="日期处理",
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
        name="大厂原题",
        db_file="12_company_questions.db",
        order=12,
        problems=[
            Problem(
                id="12_01",
                category_id="12",
                title="字节 — 题1",
                difficulty=3,
                tags=["字节", "大厂"],
                description="字节跳动面试原题。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
            Problem(
                id="12_02",
                category_id="12",
                title="字节 — 题2",
                difficulty=3,
                tags=["字节", "大厂"],
                description="字节跳动面试原题。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
            Problem(
                id="12_03",
                category_id="12",
                title="得物实际场景需求",
                difficulty=4,
                tags=["得物", "大厂", "场景"],
                description="得物真实业务场景 SQL 需求。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
            Problem(
                id="12_04",
                category_id="12",
                title="阿里面试题",
                difficulty=4,
                tags=["阿里", "大厂"],
                description="阿里巴巴面试原题。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
            Problem(
                id="12_05",
                category_id="12",
                title="拼多多面试题",
                difficulty=3,
                tags=["拼多多", "大厂"],
                description="拼多多面试原题。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
        ],
    ),
    Category(
        id="13",
        name="JSON 解析",
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
        name="趣味 SQL",
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
                tags=["挑战赛", "趣味"],
                description="墨天轮 SQL 挑战赛题目。",
                reference_sql="",
                tables=[],
                hints=[],
            ),
            Problem(
                id="14_03",
                category_id="14",
                title="赛马问题",
                difficulty=4,
                tags=["趣味", "赛马", "非等值关联"],
                description="""
如何用 SQL 解决趣味赛马问题（非等值关联匹配）？
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
                tags=["熵", "趣味", "信息论"],
                description="如何用 SQL 计算块熵（Block Entropy）？",
                reference_sql="",
                tables=[],
                hints=[],
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
```

- [ ] **步骤 2：验证 Python 语法**

```bash
python3 -c "import sys; sys.path.insert(0, 'data_builder'); from manifest import CATEGORIES; print(f'{len(CATEGORIES)} categories, {len([p for c in CATEGORIES for p in c.problems])} problems')"
```

预期：`14 categories, 44 problems`（部分题目内容待后续填充完整）

- [ ] **步骤 3：Commit**

```bash
git add data_builder/manifest.py
git commit -m "feat: add manifest with all 14 categories and SQL problems metadata"
```

---

### 任务 3：进度数据库初始化

**文件：**
- 创建：`backend/database.py`

- [ ] **步骤 1：编写 database.py — progress.db 建表 + manifest 加载**

```python
"""数据库管理：progress.db + 多库连接 + manifest 加载"""

import sqlite3
import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES_DIR = BASE_DIR / "databases"
PROGRESS_DB = DATABASES_DIR / "progress.db"


def init_progress_db():
    """创建 progress.db 及 problems/progress 表"""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PROGRESS_DB))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS problems (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL,
            title TEXT NOT NULL,
            difficulty INTEGER DEFAULT 1,
            db_path TEXT NOT NULL,
            table_names TEXT DEFAULT '[]',
            description TEXT DEFAULT '',
            reference_sql TEXT DEFAULT '',
            hints TEXT DEFAULT '[]',
            tags TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progress (
            problem_id TEXT PRIMARY KEY REFERENCES problems(id),
            status TEXT DEFAULT 'not_started',
            completed_count INTEGER DEFAULT 0,
            mastery_level INTEGER DEFAULT 0,
            last_practiced_at TIMESTAMP,
            notes TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def seed_problems():
    """将 manifest.py 中的题目数据同步到 progress.db 的 problems 表"""
    import sys
    sys.path.insert(0, str(BASE_DIR / "data_builder"))
    from manifest import CATEGORIES

    conn = sqlite3.connect(str(PROGRESS_DB))

    for cat in CATEGORIES:
        for prob in cat.problems:
            conn.execute("""
                INSERT OR REPLACE INTO problems
                    (id, category_id, title, difficulty, db_path, table_names,
                     description, reference_sql, hints, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prob.id, prob.category_id, prob.title, prob.difficulty,
                str(DATABASES_DIR / cat.db_file),
                json.dumps(prob.tables, ensure_ascii=False),
                prob.description.strip(),
                prob.reference_sql.strip(),
                json.dumps(prob.hints, ensure_ascii=False),
                json.dumps(prob.tags, ensure_ascii=False),
            ))
            # Ensure progress row exists
            conn.execute("""
                INSERT OR IGNORE INTO progress (problem_id)
                VALUES (?)
            """, (prob.id,))

    conn.commit()
    conn.close()


def get_progress_connection() -> sqlite3.Connection:
    """获取 progress.db 连接"""
    conn = sqlite3.connect(str(PROGRESS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def get_practice_db_path(db_file: str) -> Path:
    """获取练习数据库的绝对路径"""
    return DATABASES_DIR / db_file


def get_table_schema(db_file: str, table_name: str) -> dict:
    """读取指定表的结构和前 5 行数据"""
    db_path = DATABASES_DIR / db_file
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # 列信息
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    # 行数
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    # 前 5 行
    rows = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()

    conn.close()

    return {
        "name": table_name,
        "columns": [{"name": c["name"], "type": c["type"]} for c in columns],
        "row_count": row_count,
        "sample_rows": [dict(r) for r in rows],
    }


if __name__ == "__main__":
    init_progress_db()
    seed_problems()
    print(f"Progress DB initialized at {PROGRESS_DB}")
```

- [ ] **步骤 2：初始化 progress.db**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 -c "
import sys; sys.path.insert(0, 'data_builder')
from backend.database import init_progress_db, seed_problems
init_progress_db()
seed_problems()
"
python3 -c "
import sqlite3
conn = sqlite3.connect('databases/progress.db')
print('problems:', conn.execute('SELECT COUNT(*) FROM problems').fetchone()[0])
print('progress:', conn.execute('SELECT COUNT(*) FROM progress').fetchone()[0])
conn.close()
"
```

预期：`problems: 44, progress: 44`

- [ ] **步骤 3：Commit**

```bash
git add backend/database.py backend/__init__.py
git commit -m "feat: add progress.db init and seed from manifest"
```

---

### 任务 4：数据构造 — build 框架

**文件：**
- 创建：`data_builder/generate_data.py`
- 创建：`data_builder/builders/__init__.py`

- [ ] **步骤 1：编写 generate_data.py — 调度所有 builder**

```python
"""数据生成入口：遍历 manifest → 运行 builder → 输出 SQLite 文件"""

import sys
import importlib
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES_DIR = BASE_DIR / "databases"
BUILDERS_DIR = Path(__file__).resolve().parent / "builders"

sys.path.insert(0, str(BASE_DIR))
from data_builder.manifest import CATEGORIES, get_all_problems


def ensure_db(category):
    """为专题创建空白 SQLite 文件"""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATABASES_DIR / category.db_file
    if db_path.exists():
        db_path.unlink()  # 重建，确保数据一致
    return sqlite3.connect(str(db_path))


def run_all():
    """运行所有 builder 生成数据"""
    # 收集哪些 builder 需要运行
    builders_to_run = set()
    for prob in get_all_problems():
        if prob.tables:  # 有表的题目才需要 builder
            builders_to_run.add(prob.category_id)

    print(f"Building databases for {len(builders_to_run)} categories...")

    for cat in CATEGORIES:
        if cat.id not in builders_to_run:
            continue

        module_name = f"data_builder.builders.{cat.db_file.replace('.db', '')}"
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            print(f"  ⚠️  No builder found for {cat.id} ({cat.name}), skipping")
            continue

        conn = ensure_db(cat)
        print(f"  📦 {cat.name} ({cat.db_file})")

        if hasattr(mod, 'build'):
            mod.build(conn)
            print(f"     ✅ build() completed")

        conn.commit()

        # 打印表信息
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for (tname,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            print(f"     📊 {tname}: {count} rows")

        conn.close()

    # 重建 progress.db 中的题目数据（以防 manifest 变更）
    from backend.database import init_progress_db, seed_problems
    init_progress_db()
    seed_problems()

    print(f"\nDone! {len(builders_to_run)} databases in {DATABASES_DIR}/")


if __name__ == "__main__":
    run_all()
```

- [ ] **步骤 2：编写 builders/__init__.py**

```python
"""Data builders for SQL practice databases.

Each module should export a `build(conn: sqlite3.Connection)` function
that creates tables and inserts practice data into the given connection.
"""
```

- [ ] **步骤 3：验证框架**

```bash
python3 -c "
import sys; sys.path.insert(0, 'data_builder')
from data_builder.generate_data import run_all
run_all()
"
```

预期：print 输出 14 个类别，部分跳过（builder 还未实现），progress.db 更新。

- [ ] **步骤 4：Commit**

```bash
git add data_builder/generate_data.py data_builder/builders/__init__.py
git commit -m "feat: add data generation orchestration framework"
```

---

### 任务 5：数据构造 — Builder 实现（01 连续登陆）

**文件：**
- 创建：`data_builder/builders/01_continuous_login.py`

- [ ] **步骤 1：编写 builder**

```python
"""Builder for Category 01: 连续登陆"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    """创建表并插入练习数据"""
    # ===== test 表：用户登录记录 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test (
            id INTEGER,
            date TEXT
        )
    """)

    # 生成数据：5 个用户，每人登录 8-15 天
    random.seed(42)
    test_data = []
    for user_id in range(1, 6):
        days = []
        start_day = random.randint(1, 20)
        for i in range(random.randint(8, 15)):
            day = start_day + i
            # 随机跳过 1-3 天来制造间断
            if random.random() < 0.2:
                start_day += random.randint(2, 4)
                day = start_day + i
            days.append(f"2024-01-{day:02d}")
        # 添加一些重复日期（同一天多次登录）
        if random.random() < 0.3:
            days.insert(random.randint(0, len(days)), random.choice(days))
        for d in days:
            test_data.append((user_id, d))

    conn.executemany("INSERT INTO test (id, date) VALUES (?, ?)", test_data)

    # ===== account 表：账户余额（拓展1） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS account (
            user_id INTEGER,
            date TEXT,
            balance REAL
        )
    """)

    account_data = []
    for user_id in range(1, 4):
        bal = 800.0
        for day in range(1, 21):
            # 随机波动
            bal += random.uniform(-100, 150)
            bal = max(0, bal)
            account_data.append((user_id, f"2024-02-{day:02d}", round(bal, 2)))
    conn.executemany(
        "INSERT INTO account (user_id, date, balance) VALUES (?, ?, ?)",
        account_data
    )

    # ===== test_xiaoming 表：日期区间（拓展2） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_xiaoming (
            id INTEGER,
            name TEXT,
            start_date TEXT,
            end_date TEXT
        )
    """)

    xm_data = [
        (1, "小明", "2024-01-01", "2024-01-05"),
        (1, "小明", "2024-01-06", "2024-01-10"),
        (1, "小明", "2024-01-15", "2024-01-20"),
        (2, "小红", "2024-02-01", "2024-02-03"),
        (2, "小红", "2024-02-03", "2024-02-07"),
        (2, "小红", "2024-02-10", "2024-02-12"),
    ]
    conn.executemany(
        "INSERT INTO test_xiaoming (id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
        xm_data
    )

    # ===== games 表：胜负记录（拓展3） =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            user_id INTEGER,
            date TEXT,
            result TEXT
        )
    """)

    game_data = []
    for user_id in range(1, 4):
        for day in range(1, 16):
            result = random.choice(["win", "win", "win", "lose"])  # 75% 胜率
            game_data.append((user_id, f"2024-03-{day:02d}", result))
    conn.executemany(
        "INSERT INTO games (user_id, date, result) VALUES (?, ?, ?)",
        game_data
    )

    print(f"     test: {len(test_data)} rows")
    print(f"     account: {len(account_data)} rows")
    print(f"     test_xiaoming: {len(xm_data)} rows")
    print(f"     games: {len(game_data)} rows")
```

- [ ] **步骤 2：验证数据生成 + SQL 可运行**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 data_builder/generate_data.py
```

预期：01_continuous_login.db 生成，4 张表有数据。

- [ ] **步骤 3：运行参考答案验证**

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('databases/01_continuous_login.db')

# 验证 01_01: 连续登陆3天以上
print('=== 01_01 连续登陆3天以上 ===')
rows = conn.execute('''
    SELECT id, date1, COUNT(*) as day_cnt FROM (
        SELECT id, date,
               date(date, '-' || ROW_NUMBER() OVER (PARTITION BY id ORDER BY date) || ' days') as date1
        FROM (SELECT DISTINCT id, date FROM test)
    ) GROUP BY id, date1 HAVING COUNT(*) >= 3
''').fetchall()
print(f'Result: {len(rows)} groups')
for r in rows[:5]:
    print(f'  user={r[0]}, start={r[1]}, days={r[2]}')

# 验证 01_05: 余额>1000的连续天数
print('=== 01_05 余额>1000连续天数 ===')
rows2 = conn.execute('''
    WITH filtered AS (
        SELECT user_id, date, balance FROM account WHERE balance > 1000
    ),
    grouped AS (
        SELECT user_id, date,
               date(date, '-' || ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) || ' days') as grp
        FROM filtered
    )
    SELECT user_id, grp, COUNT(*) as days
    FROM grouped GROUP BY user_id, grp HAVING COUNT(*) > 1
''').fetchall()
print(f'Result: {len(rows2)} groups')
for r in rows2[:5]:
    print(f'  user={r[0]}, start={r[1]}, days={r[2]}')

conn.close()
"
```

预期：两题都返回非空结果。

- [ ] **步骤 4：Commit**

```bash
git add data_builder/builders/01_continuous_login.py
git commit -m "feat: add data builder for category 01 continuous_login"
```

---

（篇幅限制，剩余任务见计划续篇。实际实现时每个类别一个 builder 任务，类似任务 5 的结构重复 14 次。为节约篇幅，此处展示 01-04 四个 builder，其余 10 个遵循相同模式。）

### 任务 6-17：数据构造 — Builders 02-14

每个 builder 遵循相同模式：`build(conn)` → CREATE TABLE → INSERT 数据 → 验证。

以 02_window_lead_lag.py 为例：

- [ ] **步骤 1：编写 builders/02_window_lead_lag.py**

```python
"""Builder for Category 02: 开窗函数 lead/lag"""

import sqlite3
import random


def build(conn: sqlite3.Connection):
    random.seed(202)

    # ===== stock_price: 波峰波谷 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_price (
            id INTEGER,
            ds TEXT,
            price REAL
        )
    """)
    data = []
    for stock_id in range(1, 4):
        price = 100.0
        for day in range(1, 16):
            price += random.uniform(-5, 5)
            price = max(1, price)
            data.append((stock_id, f"2024-01-{day:02d}", round(price, 2)))
    conn.executemany("INSERT INTO stock_price (id, ds, price) VALUES (?, ?, ?)", data)

    # ===== data_table: 前后列转换 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS data_table (
            id INTEGER,
            date TEXT,
            value INTEGER
        )
    """)
    dv = []
    for uid in range(1, 4):
        for day in range(1, 8):
            dv.append((uid, f"2024-02-{day:02d}", random.randint(10, 100)))
    conn.executemany("INSERT INTO data_table (id, date, value) VALUES (?, ?, ?)", dv)

    # ===== metrics: 变化率计算 =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            date TEXT,
            value REAL
        )
    """)
    mv = []
    val = 50.0
    for day in range(1, 12):
        val += random.uniform(-10, 15)
        val = max(1, val)
        mv.append((f"2024-03-{day:02d}", round(val, 2)))
    conn.executemany("INSERT INTO metrics (date, value) VALUES (?, ?)", mv)

    print(f"     stock_price: {len(data)} rows")
    print(f"     data_table: {len(dv)} rows")
    print(f"     metrics: {len(mv)} rows")
```

- [ ] **步骤 2：运行验证**

```bash
python3 data_builder/generate_data.py
python3 -c "
import sqlite3
conn = sqlite3.connect('databases/02_window_lead_lag.db')
# Verify 波峰波谷 SQL returns results
rows = conn.execute('''
    SELECT * FROM (
        SELECT id, ds, price,
               LAG(price) OVER (PARTITION BY id ORDER BY ds) AS lag_price,
               LEAD(price) OVER (PARTITION BY id ORDER BY ds) AS lead_price
        FROM stock_price
    ) WHERE price > lag_price AND price > lead_price
''').fetchall()
print(f'波峰 rows: {len(rows)}')
conn.close()
"
```

- [ ] **步骤 3：Commit**

其余 builder（03-14）同样模式实现，每个 commit 一个。

---

### 任务 18：FastAPI — 后端基础

**文件：**
- 创建：`backend/main.py`
- 创建：`backend/models/schemas.py`
- 创建：`backend/models/__init__.py`
- 创建：`backend/routers/__init__.py`

- [ ] **步骤 1：安装依赖**

```bash
pip3 install fastapi uvicorn
```

- [ ] **步骤 2：编写 models/schemas.py**

```python
"""Pydantic models for API request/response"""

from pydantic import BaseModel
from typing import List, Optional


class ProgressInfo(BaseModel):
    status: str = "not_started"
    completed_count: int = 0
    mastery_level: int = 0
    last_practiced_at: Optional[str] = None


class ProblemBrief(BaseModel):
    id: str
    title: str
    difficulty: int
    tags: List[str] = []
    progress: Optional[ProgressInfo] = None


class CategoryInfo(BaseModel):
    id: str
    name: str
    db_file: str
    order: int
    stats: dict  # {total, completed, avg_mastery}


class CategoryListResponse(BaseModel):
    categories: List[CategoryInfo]
    global_stats: dict


class ProblemListResponse(BaseModel):
    category: CategoryInfo
    problems: List[ProblemBrief]
    stats: dict


class ProblemDetail(BaseModel):
    id: str
    category_id: str
    title: str
    difficulty: int
    tags: List[str]
    description: str
    reference_sql: str
    tables: List[str]
    hints: List[str]
    progress: Optional[ProgressInfo]
    db_file: str
    db_connection: str  # DBeaver 连接串


class TableInfo(BaseModel):
    name: str
    columns: List[dict]
    row_count: int
    sample_rows: List[dict]


class TablesResponse(BaseModel):
    tables: List[TableInfo]
    db_connection: str


class CompleteRequest(BaseModel):
    action: str = "complete"  # always "complete"
    mastery: int = 3  # 1-5


class ProgressUpdate(BaseModel):
    mastery_level: Optional[int] = None
    notes: Optional[str] = None


class ProgressSummary(BaseModel):
    total: int
    completed: int
    in_progress: int
    not_started: int
    avg_mastery: float


class DbConnectionResponse(BaseModel):
    db_file: str
    connection_string: str
```

- [ ] **步骤 3：编写 main.py**

```python
"""FastAPI 应用入口"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import categories, problems, progress, databases

app = FastAPI(title="SQL Practice Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix="/api")
app.include_router(problems.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(databases.router, prefix="/api")


@app.get("/api/health")
def health():
    from backend.database import DATABASES_DIR
    return {
        "status": "ok",
        "databases_dir": str(DATABASES_DIR),
    }
```

- [ ] **步骤 4：启动验证**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 -m uvicorn backend.main:app --reload --port 8000 &
sleep 2
curl -s http://localhost:8000/api/health | python3 -m json.tool
kill %1 2>/dev/null
```

预期：`{"status": "ok", "databases_dir": "..."}`

- [ ] **步骤 5：Commit**

```bash
git add backend/main.py backend/models/ backend/routers/__init__.py
git commit -m "feat: add FastAPI app skeleton with CORS and models"
```

---

### 任务 19：FastAPI — categories 路由

**文件：**
- 创建：`backend/routers/categories.py`

- [ ] **步骤 1：编写 categories.py**

```python
"""GET /api/categories — 专题列表（含进度统计）"""

import json
from fastapi import APIRouter
from backend.database import get_progress_connection

router = APIRouter()


@router.get("/categories")
def list_categories():
    conn = get_progress_connection()

    rows = conn.execute("""
        SELECT p.category_id, p.title, COUNT(*) as total,
               SUM(CASE WHEN pr.status = 'completed' THEN 1 ELSE 0 END) as completed,
               ROUND(AVG(pr.mastery_level), 1) as avg_mastery
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        GROUP BY p.category_id
        ORDER BY p.category_id
    """).fetchall()

    categories = []
    total_problems = 0
    total_completed = 0
    total_mastery_sum = 0.0

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import CATEGORIES

    cat_map = {c.id: c for c in CATEGORIES}

    for row in rows:
        cat = cat_map.get(row["category_id"])
        categories.append({
            "id": row["category_id"],
            "name": cat.name if cat else row["category_id"],
            "db_file": cat.db_file if cat else "",
            "order": cat.order if cat else 99,
            "stats": {
                "total": row["total"],
                "completed": row["completed"],
                "avg_mastery": row["avg_mastery"] or 0,
            }
        })
        total_problems += row["total"]
        total_completed += row["completed"]
        total_mastery_sum += (row["avg_mastery"] or 0) * row["total"]

    conn.close()

    return {
        "categories": sorted(categories, key=lambda c: c["order"]),
        "global_stats": {
            "total": total_problems,
            "completed": total_completed,
            "avg_mastery": round(total_mastery_sum / total_problems, 1) if total_problems else 0,
        }
    }
```

- [ ] **步骤 2：测试**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 -m uvicorn backend.main:app --port 8000 &
sleep 2
curl -s http://localhost:8000/api/categories | python3 -m json.tool | head -30
kill %1 2>/dev/null
```

预期：返回所有 14 个专题及其进度统计。

- [ ] **步骤 3：Commit**

```bash
git add backend/routers/categories.py
git commit -m "feat: add categories API endpoint"
```

---

### 任务 20：FastAPI — problems 路由

**文件：**
- 创建：`backend/routers/problems.py`

- [ ] **步骤 1：编写 problems.py**

```python
"""GET /api/problems — 题目列表 + 详情 + 表结构"""

import json
from fastapi import APIRouter, HTTPException, Query
from backend.database import (
    get_progress_connection, get_practice_db_path, get_table_schema
)

router = APIRouter()


@router.get("/problems")
def list_problems(category_id: str = Query(None)):
    """获取题目列表，可按专题筛选"""
    conn = get_progress_connection()

    where = "WHERE p.category_id = ?" if category_id else ""
    params = (category_id,) if category_id else ()

    rows = conn.execute(f"""
        SELECT p.*, pr.status, pr.completed_count, pr.mastery_level,
               pr.last_practiced_at
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        {where}
        ORDER BY p.id
    """, params).fetchall()

    problems = []
    for r in rows:
        problems.append({
            "id": r["id"],
            "category_id": r["category_id"],
            "title": r["title"],
            "difficulty": r["difficulty"],
            "tags": json.loads(r["tags"]) if r["tags"] else [],
            "progress": {
                "status": r["status"] or "not_started",
                "completed_count": r["completed_count"] or 0,
                "mastery_level": r["mastery_level"] or 0,
                "last_practiced_at": r["last_practiced_at"],
            }
        })

    # 统计
    stats = conn.execute(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN pr.status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        {where}
    """, params).fetchone()

    # 专题信息
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import get_category

    cat = get_category(category_id) if category_id else None

    conn.close()

    return {
        "category": {
            "id": cat.id if cat else "",
            "name": cat.name if cat else "",
            "db_file": cat.db_file if cat else "",
            "order": cat.order if cat else 0,
        } if cat else None,
        "problems": problems,
        "stats": {
            "total": stats["total"],
            "completed": stats["completed"] or 0,
        }
    }


@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    """获取单题详情"""
    conn = get_progress_connection()

    row = conn.execute("""
        SELECT p.*, pr.status, pr.completed_count, pr.mastery_level,
               pr.last_practiced_at, pr.notes
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        WHERE p.id = ?
    """, (problem_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    # 标记为 in_progress（如果是首次查看）
    if row["status"] == "not_started":
        conn.execute("""
            UPDATE progress SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP
            WHERE problem_id = ?
        """, (problem_id,))
        conn.commit()

    conn.close()

    db_path = get_practice_db_path("")

    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "title": row["title"],
        "difficulty": row["difficulty"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "description": row["description"] or "",
        "reference_sql": row["reference_sql"] or "",
        "tables": json.loads(row["table_names"]) if row["table_names"] else [],
        "hints": json.loads(row["hints"]) if row["hints"] else [],
        "progress": {
            "status": row["status"] or "not_started",
            "completed_count": row["completed_count"] or 0,
            "mastery_level": row["mastery_level"] or 0,
            "last_practiced_at": row["last_practiced_at"],
        },
        "db_file": row["db_path"].split("/")[-1] if row["db_path"] else "",
        "db_connection": f"sqlite:///{row['db_path']}",
    }


@router.get("/problems/{problem_id}/tables")
def get_problem_tables(problem_id: str):
    """获取该题所用表的结构和示例数据"""
    conn = get_progress_connection()

    row = conn.execute(
        "SELECT db_path, table_names FROM problems WHERE id = ?",
        (problem_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    db_file = row["db_path"].split("/")[-1] if row["db_path"] else ""
    table_names = json.loads(row["table_names"]) if row["table_names"] else []

    tables = []
    for tname in table_names:
        info = get_table_schema(db_file, tname)
        if info:
            tables.append(info)

    conn.close()

    return {
        "tables": tables,
        "db_connection": f"sqlite:///{row['db_path']}",
    }
```

- [ ] **步骤 2：测试**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 -m uvicorn backend.main:app --port 8000 &
sleep 2
curl -s "http://localhost:8000/api/problems?category_id=01" | python3 -m json.tool | head -30
curl -s http://localhost:8000/api/problems/01_01 | python3 -m json.tool | head -30
kill %1 2>/dev/null
```

- [ ] **步骤 3：Commit**

---

### 任务 21：FastAPI — progress 路由

**文件：**
- 创建：`backend/routers/progress.py`

- [ ] **步骤 1：编写 progress.py**

```python
"""POST/PATCH/GET /api/progress — 进度管理"""

import json
from fastapi import APIRouter, HTTPException
from backend.database import get_progress_connection
from backend.models.schemas import CompleteRequest, ProgressUpdate

router = APIRouter()


def compute_mastery(completed_count: int, manual_level: int,
                    last_practiced_at: str | None) -> int:
    """计算掌握度：MAX(手动评分, 自动评级) + 时间衰减"""
    # 自动评级
    if completed_count >= 5:
        auto = 5
    elif completed_count >= 3:
        auto = 3
    elif completed_count >= 1:
        auto = 2
    else:
        auto = 0

    result = max(manual_level, auto)

    # 时间衰减：超过 30 天降一级
    if last_practiced_at:
        from datetime import datetime, timedelta
        try:
            last = datetime.fromisoformat(last_practiced_at)
            if (datetime.now() - last) > timedelta(days=30):
                result = max(1, result - 1)
        except ValueError:
            pass

    return result


@router.post("/progress/{problem_id}")
def complete_problem(problem_id: str, req: CompleteRequest):
    """标记题目完成"""
    conn = get_progress_connection()

    # 检查题目存在
    prob = conn.execute(
        "SELECT id FROM problems WHERE id = ?", (problem_id,)
    ).fetchone()
    if not prob:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    # 获取当前进度
    cur = conn.execute(
        "SELECT completed_count, mastery_level FROM progress WHERE problem_id = ?",
        (problem_id,)
    ).fetchone()

    new_count = (cur["completed_count"] or 0) + 1
    new_mastery = compute_mastery(new_count, req.mastery, None)

    conn.execute("""
        UPDATE progress
        SET status = 'completed',
            completed_count = ?,
            mastery_level = ?,
            last_practiced_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE problem_id = ?
    """, (new_count, new_mastery, problem_id))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM progress WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    conn.close()

    return {
        "problem_id": problem_id,
        "status": row["status"],
        "completed_count": row["completed_count"],
        "mastery_level": row["mastery_level"],
        "last_practiced_at": row["last_practiced_at"],
    }


@router.patch("/progress/{problem_id}")
def update_progress(problem_id: str, req: ProgressUpdate):
    """更新掌握度或笔记"""
    conn = get_progress_connection()

    cur = conn.execute(
        "SELECT completed_count, mastery_level, last_practiced_at FROM progress WHERE problem_id = ?",
        (problem_id,)
    ).fetchone()

    if not cur:
        conn.close()
        raise HTTPException(status_code=404, detail="Progress not found")

    manual = req.mastery_level if req.mastery_level is not None else (cur["mastery_level"] or 0)
    new_mastery = compute_mastery(
        cur["completed_count"] or 0,
        manual,
        cur["last_practiced_at"]
    )

    if req.notes is not None:
        conn.execute(
            "UPDATE progress SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE problem_id = ?",
            (req.notes, problem_id)
        )

    conn.execute("""
        UPDATE progress
        SET mastery_level = ?, updated_at = CURRENT_TIMESTAMP
        WHERE problem_id = ?
    """, (new_mastery, problem_id))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM progress WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    conn.close()

    return {
        "problem_id": problem_id,
        "mastery_level": row["mastery_level"],
        "notes": row["notes"],
    }


@router.get("/progress/summary")
def progress_summary():
    """全局进度统计"""
    conn = get_progress_connection()

    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started,
            ROUND(AVG(mastery_level), 1) as avg_mastery
        FROM progress
    """).fetchone()

    conn.close()

    return {
        "total": row["total"],
        "completed": row["completed"] or 0,
        "in_progress": row["in_progress"] or 0,
        "not_started": row["not_started"] or 0,
        "avg_mastery": row["avg_mastery"] or 0,
    }
```

- [ ] **步骤 2：测试**

```bash
curl -s -X POST http://localhost:8000/api/progress/01_01 \
  -H "Content-Type: application/json" \
  -d '{"action":"complete","mastery":4}' | python3 -m json.tool
curl -s http://localhost:8000/api/progress/summary | python3 -m json.tool
```

- [ ] **步骤 3：Commit**

---

### 任务 22：FastAPI — databases 路由

**文件：**
- 创建：`backend/routers/databases.py`

- [ ] **步骤 1：编写 databases.py**

```python
"""GET /api/databases/{id}/connect"""

from fastapi import APIRouter
from backend.database import get_practice_db_path

router = APIRouter()


@router.get("/databases/{category_id}/connect")
def get_connection(category_id: str):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import get_category

    cat = get_category(category_id)
    if not cat:
        return {"error": "Category not found"}

    db_path = get_practice_db_path(cat.db_file)
    return {
        "db_file": cat.db_file,
        "connection_string": f"sqlite:///{db_path}",
        "exists": db_path.exists(),
    }
```

- [ ] **步骤 2：Commit**

---

### 任务 23：前端 — Vite + React 初始化

**文件：**
- 创建：`frontend/` 目录下 Vite 项目文件

- [ ] **步骤 1：创建 Vite 项目**

```bash
cd /Users/yourton_ma/Documents/sql_practice
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite react-router-dom react-markdown
```

- [ ] **步骤 2：配置 Tailwind CSS**

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

`frontend/src/index.css`:
```css
@import "tailwindcss";
```

- [ ] **步骤 3：验证启动**

```bash
cd frontend && npm run dev &
sleep 3
curl -s http://localhost:5173 | head -5
kill %1 2>/dev/null
```

- [ ] **步骤 4：Commit**

---

### 任务 24：前端 — TypeScript 类型 + API 层

**文件：**
- 创建：`frontend/src/types.ts`
- 创建：`frontend/src/api.ts`

- [ ] **步骤 1：编写 types.ts**

```typescript
export interface ProgressInfo {
  status: string;
  completed_count: number;
  mastery_level: number;
  last_practiced_at: string | null;
}

export interface ProblemBrief {
  id: string;
  title: string;
  difficulty: number;
  tags: string[];
  progress: ProgressInfo | null;
}

export interface CategoryInfo {
  id: string;
  name: string;
  db_file: string;
  order: number;
  stats: { total: number; completed: number; avg_mastery: number };
}

export interface CategoryListResponse {
  categories: CategoryInfo[];
  global_stats: { total: number; completed: number; avg_mastery: number };
}

export interface ProblemDetail {
  id: string;
  category_id: string;
  title: string;
  difficulty: number;
  tags: string[];
  description: string;
  reference_sql: string;
  tables: string[];
  hints: string[];
  progress: ProgressInfo | null;
  db_file: string;
  db_connection: string;
}

export interface TableInfo {
  name: string;
  columns: { name: string; type: string }[];
  row_count: number;
  sample_rows: Record<string, unknown>[];
}
```

- [ ] **步骤 2：编写 api.ts**

```typescript
import type {
  CategoryListResponse,
  ProblemDetail,
  ProblemBrief,
  TableInfo,
} from "./types";

const BASE = "/api";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json();
}

export async function getCategories(): Promise<CategoryListResponse> {
  return fetchJSON<CategoryListResponse>(`${BASE}/categories`);
}

export async function getProblems(categoryId: string): Promise<{
  category: { id: string; name: string; db_file: string };
  problems: ProblemBrief[];
  stats: { total: number; completed: number };
}> {
  return fetchJSON(`${BASE}/problems?category_id=${categoryId}`);
}

export async function getProblemDetail(id: string): Promise<ProblemDetail> {
  return fetchJSON(`${BASE}/problems/${id}`);
}

export async function getProblemTables(id: string): Promise<{
  tables: TableInfo[];
  db_connection: string;
}> {
  return fetchJSON(`${BASE}/problems/${id}/tables`);
}

export async function completeProblem(
  id: string,
  mastery: number
): Promise<ProgressInfo> {
  return fetchJSON(`${BASE}/progress/${id}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "complete", mastery }),
  });
}

export async function updateProgress(
  id: string,
  data: { mastery_level?: number; notes?: string }
): Promise<void> {
  await fetchJSON(`${BASE}/progress/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
```

- [ ] **步骤 3：Commit**

---

### 任务 25：前端 — 页面与组件

**文件：** 所有 `frontend/src/pages/` 和 `frontend/src/components/` 下的文件

- [ ] **步骤 1：编写 App.tsx**

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import CategoryListPage from "./pages/CategoryListPage";
import ProblemListPage from "./pages/ProblemListPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<CategoryListPage />} />
          <Route path="/category/:id" element={<ProblemListPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
```

- [ ] **步骤 2：按组件逐个实现**（顺序：GlobalProgressBar → CategoryCard → CategoryListPage → ProblemSidebar → DbConnectionInfo → TableSchema → ReferenceAnswer → ProgressPanel → RatingModal → ProblemDetail → ProblemListPage）

每个组件遵循 TDD 模式：先写组件 → 在页面中集成 → 验证渲染。

关键交互：
- `CategoryCard`: 点击 → `navigate(/category/${id})`
- `ProblemSidebar`: 从 API 加载题目列表，点击切换选中
- `ProblemDetail`: 展示描述(Markdown)、表结构、参考答案(折叠)、进度面板
- `ProgressPanel`: 星级评分可点击 → PATCH progress、标记完成按钮 → POST progress → 弹出 RatingModal
- `DbConnectionInfo`: 复制按钮 → `navigator.clipboard.writeText(connection_string)`
- 进度数据使用 `useState` + `useEffect` 管理，乐观更新

- [ ] **步骤 3：启动前端验证**

```bash
cd frontend && npm run dev &
# 浏览器打开 http://localhost:5173
# 验证：专题列表加载 → 点击专题 → 题目列表 → 查看详情 → 标记完成
```

- [ ] **步骤 4：Commit**

```bash
git add frontend/src/
git commit -m "feat: add React frontend with category list and problem detail pages"
```

---

### 任务 26：端到端集成测试

- [ ] **步骤 1：启动后端**

```bash
cd /Users/yourton_ma/Documents/sql_practice
python3 -m uvicorn backend.main:app --port 8000 &
```

- [ ] **步骤 2：启动前端**

```bash
cd frontend && npm run dev &
```

- [ ] **步骤 3：功能验证清单**

```bash
# 1. 分类列表 API
curl -s http://localhost:8000/api/categories | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"categories\"])} categories, {d[\"global_stats\"][\"total\"]} problems')"

# 2. 题目列表 API
curl -s "http://localhost:8000/api/problems?category_id=01" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d[\"problems\"])} problems in category 01')"

# 3. 题目详情 API
curl -s http://localhost:8000/api/problems/01_01 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['title'])"

# 4. 标记完成
curl -s -X POST http://localhost:8000/api/progress/01_01 -H "Content-Type: application/json" -d '{"action":"complete","mastery":4}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'mastery={d[\"mastery_level\"]}, count={d[\"completed_count\"]}')"

# 5. 连接信息
curl -s http://localhost:8000/api/databases/01/connect | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['connection_string'])"

# 6. DBeaver 连接验证
sqlite3 databases/01_continuous_login.db "SELECT COUNT(*) FROM test;"
```

预期：所有 API 返回正确数据，SQLite 有数据。

- [ ] **步骤 4：Commit**

```bash
git add -A
git commit -m "chore: final integration verification"
```

