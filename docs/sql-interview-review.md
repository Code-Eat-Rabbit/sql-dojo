# SQL 面试复习手册

> 数据来源：本项目 `data_builder/manifest.py`（44 题，精选 21 题 + 16 题以变式/延伸吸收）。
> 方言口径：Hive SQL（面试标准），SQLite 差异处单独标注。

## 使用说明

- **日常复习**：从 Part 2 第一题开始，先只看题面和表结构，自己想 5 分钟再点开折叠块对答案。
- **面试前突击**：只过 Part 1 速查表 + 每题的"面试追问"小节。
- 想回项目重做某题：题号旁标注了项目内题号（如 `01_01`），启动项目后可直接练习。

---

# Part 1 知识速查

## 1.1 窗口函数家族总览

| 类别 | 函数 | 一句话语义 | 典型题 |
|---|---|---|---|
| 排序 | `row_number()` | 严格递增 1,2,3,4（并列也分先后） | Q1 Q3 |
| 排序 | `rank()` | 并列同号，下一个跳号 1,2,2,4 | Q6 Q8 |
| 排序 | `dense_rank()` | 并列同号，下一个不跳 1,2,2,3 | Q6 |
| 前后 | `lag(col, n, default)` | 向上取第 n 行 | Q2 Q4 Q5 |
| 前后 | `lead(col, n, default)` | 向下取第 n 行 | Q4 |
| 前后 | `first_value(col)` | 窗口帧内第一个值 | — |
| 前后 | `last_value(col)` | 窗口帧内最后一个值（默认帧不含后续行，易错） | — |
| 聚合开窗 | `sum/min/max/avg/count(col) OVER(...)` | 加 `ORDER BY` = 累计；不加 = 分组总量 | Q7 Q8 Q9 |
| 帧控制 | `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | 明确框定累计范围 | Q10 Q19 |

**帧语法速记**：`UNBOUNDED PRECEDING`（组首）→ `n PRECEDING`（前 n 行）→ `CURRENT ROW` → `n FOLLOWING`（后 n 行）→ `UNBOUNDED FOLLOWING`（组尾）。
**默认帧**：有 `ORDER BY` 时为 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`；无 `ORDER BY` 时为全组。
**ROWS vs RANGE**：ROWS 按物理行，RANGE 按排序值（同值并入同一帧）——日期去重后两者等价，未去重时会不同。

## 1.2 经典题型模式速查

| 套路 | 核心口诀 | 对应题 |
|---|---|---|
| 连续问题-差值法 | 去重 → `日期 - row_number()` 得分组键 → `GROUP BY` + `HAVING` 计数 | Q1 |
| 连续问题-lag 法 | `lag` 取前 N-1 个日期，`datediff` 全差 1 则连续 | Q2 |
| 连续问题-自关联 | 自关联 N 次，`datediff = 1` 逐级衔接 | Q2 |
| 条件连续（连胜） | 先筛出满足条件的行 → 双 `row_number` 差值分组，或 `lag+case` 造断点标记 + `sum() over` 累加分段 | Q3 |
| 区间断点分段 | `lag(end)` 与当前 `start` 比较 → `case` 造 0/1 → `sum() over` 累加成组号 → `min(start), max(end)` | Q3 Q10 |
| 波峰波谷 | `lag` 前值 + `lead` 后值 + `case when` 三比较 | Q4 |
| 环比变化率 | `lag` 取前值 → `(今-前)/前` → `round` | Q5 |
| 第 N 高 | `dense_rank() over(partition by ... order by ... desc)` 取 `= N` | Q6 |
| 累计指标 | `sum() over(partition by ... order by ...)`；首次达标 = 累计后 `where` 筛 + `min(日期)` | Q7 Q9 |
| 同时在线 | 进 +1 / 出 -1 → `union all` → `sum() over` 累加 → `max` 取峰值 | Q8 |
| 区间合并 | `max(end) over(前置行)` 滚动右端 → `start > 滚动右端` 开新组 → 按组 `min/max` | Q10 |
| 缺失值填充 | 相关子查询取"最近的非空前值"（forward fill） | Q11 |
| 全称量词（每科都>60） | 双重否定：`not in`（存在不及格的学生）；或 `group by + having min(score) > 60` | Q12 |
| 相互关注 | 自关联 `a.from=b.to and a.to=b.from`；或 `union all` 双向 + `having count>=2` | Q13 |
| N 日留存 | `min(date)` 定首活 → `left join` 第 N 天活跃 → `count(distinct)` 分子分母 | Q14 |
| 行转列（炸裂） | Hive：`lateral view explode(split(col, ','))`；SQLite：递归 CTE 模拟 | Q15 |
| 列转行（聚合） | Hive：`concat_ws(',', collect_list(col))`；SQLite：`group_concat` | Q16 |
| 接雨水 | 每位储水 = `least(左滚动max, 右滚动max) - 当前高`，两侧 `max() over` 求出 | Q19 |
| 找相邻更快者 | 非等值 join `b.time < a.time` + 取 `min`；更优：`lag() over(order by time)` | Q20 |

## 1.3 JOIN 类型速查

| 类型 | 语义 | 典型题 |
|---|---|---|
| inner join | 只留两边都匹配的行 | Q13 |
| left join | 保左表全量，右表缺失补 NULL（留存题分母不丢的关键） | Q14 |
| full outer join | 两边全保 | — |
| 自关联 | 同表 join 两次（a/b 别名），用于"相互关注""日期衔接" | Q2 Q13 |
| 非等值 join | 条件不是 `=` 而是 `<`/`>` 等，会产生数据放大，注意行数 | Q20 |
| lateral view | Hive 表生成函数配合，一行变多行 | Q15 Q18 |

**NOT IN 陷阱**（面试高频）：子查询结果集含 NULL 时，`NOT IN` 整体返回空。规避：`NOT EXISTS`，或子查询加 `WHERE col IS NOT NULL`。

## 1.4 日期与字符串函数速查（Hive 口径）

| 目标 | 写法 | 备注 |
|---|---|---|
| 年 | `substr(date, 1, 4)` 或 `year(date)` | 11_01 即此 |
| 月 | `substr(date, 6, 2)` 或 `month(date)` | |
| 季度 | `concat(substr(date,1,4), 'Q', cast((month(date)-1)/3+1 as string))` | 公式 `(m-1)/3+1` 必会手写 |
| 半年 | 同上，`(m-1)/6+1` | |
| 年月 | `substr(date, 1, 7)` 或 `date_format(date,'yyyy-MM')` | |
| 日期差 | `datediff(a, b)`（a-b 天数） | Q1 Q2 |
| 日期增减 | `date_add(d, n)` / `date_sub(d, n)`（n 可为负） | Q1 Q14 |
| 取日期部分 | `to_date('2024-01-01 10:00:00')` → `2024-01-01` | 等价 substr(d,1,10) |
| 月末 | `last_day(d)` | 滚动窗口常用 |
| 字符串截取 | `substr(s, start, len)`（1 起） | |
| 定位/分割 | `instr(s, sub)`、`split(s, ',')` | |
| 拼接 | `concat(a, b)` / `concat_ws(',', col...)`（跳过 NULL） | Q16 |

## 1.5 高频面试追问清单

1. **窗口函数 vs GROUP BY**：GROUP BY 压缩为每组一行；窗口函数保留每行、附加计算列。要"既有明细又有聚合"时只能用窗口。
2. **row_number / rank / dense_rank 怎么选**：要 TopN 去重（并列只取一个）用 row_number；名次要跳号用 rank；名次不跳号/取第 N 高用 dense_rank。
3. **COUNT(DISTINCT) 数据倾斜**：单个 reducer 聚合大维度 → 先 `group by` 预聚合打散，或两阶段 distinct、 bitmap；高维维度拆分。
4. **千亿级 join 优化**：小表广播（map-side join / mapjoin）、分桶表（bucket join，同键落同节点）、Bloom filter 预过滤、避免非等值 join 的笛卡尔放大（Q13 追问展开）。
5. **union all vs union**：union all 保留全部（含重复），进出场计数必须用 union all；union 去重触发 shuffle，代价高。
6. **Hive 与标准 SQL 差异**：`date_add(d, n)` 不是 `INTERVAL` 语法；多参取小用 `least()`（SQLite 是 `min()`）；`collect_list/collect_set` vs `group_concat`；`get_json_object` vs `json_extract`。
7. **什么时候用递归 CTE，什么时候用开窗**：先看能否用 `row_number/lag + 聚合开窗` 的"分段子问题"套路解决（连续、分段、层级汇总大多可以）；真需要逐行传递状态（如逐行 forward fill、树遍历）才用递归——面试先答开窗解法是加分项（源自题 10_01 的辨析）。

# Part 2 精选题册

## 组1 连续问题

---

### Q1. 查询连续登陆3天以上的用户 `★★☆☆☆` `字节面试题`

> 来源：项目题号 `01_01`　表：`test`

**表结构：**

| id (INTEGER) | date (TEXT) |
|---|---|
| 1 | 2024-01-01 08:00:00 |
| 1 | 2024-01-01 20:00:00 |
| 1 | 2024-01-02 09:00:00 |

给定一张用户登录表 `test`，包含字段 `id`（用户ID）和 `date`（登录日期）。
请查询连续登录 3 天以上的所有用户。

*提示：row_number() over() 减一下，再分组 count；先去重，再用 date_add + row_number 创建分组标识，最后按分组标识 count 筛选。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：经典的「差值法」套路——同一日期去重后，连续日期与 row_number 同为等差数列，两者相减差值恒定，该差值即分组键。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 步骤三：统计连续天数，筛选 > 3
SELECT id, date1, COUNT(*) AS day_cnt
FROM (
    -- 步骤二：用 row_number 标记，date_add 减去 row_number 得分组键
    SELECT id, date,
           date_add(date, -ROW_NUMBER() OVER (PARTITION BY id ORDER BY date)) AS date1
    FROM (
        -- 步骤一：按用户+日期去重（一天可能多次登录）
        SELECT id, substr(date, 1, 10) AS date
        FROM test
        GROUP BY id, substr(date, 1, 10)
    ) t1
) t2
GROUP BY id, date1
HAVING COUNT(*) > 3;
```

**3. 关键解析**：

- `substr(date, 1, 10)` 将 datetime 截为日期（`'2024-01-01 08:00:00'` → `'2024-01-01'`）。Hive 可直接用 `to_date(date)` 替代。
- `date_add(date, -ROW_NUMBER() ...)` 是核心：日期每天 +1，row_number 也 +1，作差后常数项抵消，连续段内差值恒定。

**4. 知识点延伸**：

**变式 1：求每个用户连续登录的最大天数（01_02）**

```sql
SELECT id, MAX(day_cnt) AS max_day_cnt
FROM (
    SELECT id, date1, COUNT(*) AS day_cnt
    FROM (
        SELECT id, date,
               date_add(date, -ROW_NUMBER() OVER (PARTITION BY id ORDER BY date)) AS date1
        FROM (
            SELECT id, substr(date, 1, 10) AS date
            FROM test
            GROUP BY id, substr(date, 1, 10)
        ) t1
    ) t2
    GROUP BY id, date1
) t3
GROUP BY id;
```

**变式 2：账户余额 > 1000 的连续天数（01_05 外汇公司）**

```sql
WITH filtered AS (
    -- 先筛选余额 > 1000 的行，再套差值法
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
```

> 「先过滤后连续」顺序不能反——如果先做连续再过滤，会把余额 <= 1000 的间隔日也纳入连续段。

**相关函数**：`date_sub(d, n)` 与 `date_add(d, -n)` 等价（负天数）。`GROUP BY id, date` 本身即去重——同一用户同一天只留一行。

**5. 面试追问**：

- **Q: 为什么必须先去重？** A: 一天多次登录会让 row_number 错位（同一天占多个序号），差值法失效。
- **Q: "连续 3 天以上"含不含恰好 3 天？** A: 口径要当场确认，`HAVING COUNT(*) >= 3` 与 `> 3` 一字之差。
- **Q: 为什么减 row_number 后差值会相同？** A: 日期与序号同步 +1 递增，作差后常数项抵消——本质是等差数列性质。

</details>

---

### Q2. 连续登录3天以上用户 — 三种方法汇总 `★★★☆☆` `方法汇总`

> 来源：项目题号 `01_03`　表：`test`

**表结构**：同 Q1，`test(id INTEGER, date TEXT)`

用三种不同方法实现「查询连续登录 3 天以上的用户」：
1. row_number() 法
2. lag/lead 法
3. 自关联法

*提示：三种方法核心都是找到连续日期，row_number 法最通用，建议重点掌握。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：同一问题用三种 SQL 技术路径解决，对比理解各自优劣。

**2. 参考 SQL（Hive 方言）**：

**方法 1：row_number() 差值法**（详见 Q1，此处不重复）

**方法 2：lag() 法**

```sql
SELECT DISTINCT id
FROM (
    SELECT id, date,
           LAG(date, 1) OVER (PARTITION BY id ORDER BY date) AS prev1,
           LAG(date, 2) OVER (PARTITION BY id ORDER BY date) AS prev2
    FROM (
        SELECT id, substr(date, 1, 10) AS date
        FROM test
        GROUP BY id, substr(date, 1, 10)
    ) deduped
) t
WHERE DATEDIFF(date, prev1) = 1 AND DATEDIFF(prev1, prev2) = 1;
```

**方法 3：自关联法**

```sql
SELECT DISTINCT a.id
FROM (
    SELECT id, substr(date, 1, 10) AS date
    FROM test
    GROUP BY id, substr(date, 1, 10)
) a
JOIN (
    SELECT id, substr(date, 1, 10) AS date
    FROM test
    GROUP BY id, substr(date, 1, 10)
) b ON a.id = b.id AND DATEDIFF(a.date, b.date) = 1
JOIN (
    SELECT id, substr(date, 1, 10) AS date
    FROM test
    GROUP BY id, substr(date, 1, 10)
) c ON b.id = c.id AND DATEDIFF(b.date, c.date) = 1;
```

**3. 关键解析**：

- 方法 2 用 `LAG(date, 1)` 和 `LAG(date, 2)` 取前两天，两个 `DATEDIFF` 全为 1 即连续三天。
- 方法 3 三次自关联逐级 `DATEDIFF = 1` 衔接：a→b 差 1 天，b→c 差 1 天，即 a/b/c 连续三天。

**4. 知识点延伸**：

| 方法 | 通用性 | 扩展到 N 天 | 性能 | 需要窗口函数 |
|---|---|---|---|---|
| row_number 差值法 | 任意 N 天 | 直接改 `HAVING COUNT(*) >= N` | O(n log n) | 是 |
| lag 法 | 需 N-1 个前值 | N 大时要写 N-1 个 LAG 列，不可扩展 | O(n log n) | 是 |
| 自关联法 | 需 N-1 次 JOIN | N 大时 N-1 次自关联，SQL 膨胀 | O(n^N) 最差 | 否 |

> row_number 差值法最通用，面试首选；自关联法虽性能最差，但不依赖窗口函数——部分老旧数据库或面试考察 SQL 基本功时可能问到。

**5. 面试追问**：

- **Q: N 很大（连续 30 天）用哪个？** A: row_number 差值法，lag 要写 29 个前值列，自关联要 29 次 JOIN。
- **Q: 自关联法的性能风险？** A: 每次自关联近似 n^2 次比较，大数据量必炸——仅适用于小数据集或面试展示基本功。
- **Q: datediff 方向？** A: `DATEDIFF(a, b)` = a - b（天数），别记反。

</details>

---

### Q3. 连胜数 `★★★☆☆` `胜负`

> 来源：项目题号 `01_07`　表：`games`

**表结构：**

| user_id | date | result |
|---|---|---|
| 1 | 2024-01-01 | win |
| 1 | 2024-01-02 | win |
| 1 | 2024-01-03 | lose |

计算每个用户的连胜数（最长连续胜场）。

*提示：连续类题的变体——把"连续"条件从日期改为胜负状态；把 win 的行单独拎出来，然后用 row_number 差值法。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：连续问题的变体——将"连续日期"换成"连续状态"。先用 `WHERE result = 'win'` 过滤出胜场，再用差值法或断点标记法分组计数。

**2. 参考 SQL（Hive 方言）**：

**解法 1：双 row_number 差值法**

```sql
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
```

**解法 2：lag + case 造断点标记，sum() over 累加分段**

```sql
WITH marked AS (
    SELECT user_id, date, result,
           CASE WHEN result = 'win'
                AND LAG(result) OVER (PARTITION BY user_id ORDER BY date) = 'win'
                THEN 0 ELSE 1 END AS new_streak
    FROM games
)
SELECT user_id,
       SUM(new_streak) OVER (PARTITION BY user_id ORDER BY date) AS streak_id,
       COUNT(*) AS streak_len
FROM marked
WHERE result = 'win'
GROUP BY user_id, streak_id;
```

**3. 关键解析**：

- 解法 1 中 `rn` 是全局行序，`rn2` 是 win 行内的行序。连续 win 段内两者同步递增，差值恒定；一旦插入 lose，`rn` 继续递增但 `rn2` 重置，差值跳变——形成新的分组。
- 解法 2 中 `CASE WHEN ... THEN 0 ELSE 1` 标记"新连胜段起点"为 1、延续为 0，`SUM() OVER` 累加后得到连胜段编号。

**4. 知识点延伸**：

**区间合并：断点标记 + 累加分段的经典应用（01_06 集度面试题）**

给定日期区间表 `test_xiaoming(id, name, start_date, end_date)`，合并连续或重叠的区间：

```sql
WITH t1 AS (
    SELECT id, name, start_date, end_date,
           LAG(end_date) OVER (PARTITION BY id, name ORDER BY start_date) AS lag_date,
           CASE
               WHEN date_add(LAG(end_date) OVER (PARTITION BY id, name ORDER BY start_date), 1) = start_date
               THEN 0 ELSE 1
           END AS new_group_flag
    FROM test_xiaoming
),
t2 AS (
    SELECT id, name, start_date, end_date,
           SUM(new_group_flag) OVER (PARTITION BY id, name ORDER BY start_date) AS group_id
    FROM t1
)
SELECT id, name,
       MIN(start_date) AS start_date,
       MAX(end_date) AS end_date
FROM t2
GROUP BY id, name, group_id
ORDER BY MIN(start_date), id, name;
```

> 此模式与 Q3 解法 2 同构：**「断点标记（CASE 0/1）+ SUM() OVER 累加分段」**。区别在于判定连续的条件——Q3 是"前一行也是 win"，01_06 是"前区间 end + 1 = 当前 start"。

**5. 面试追问**：

- **Q: 连续的"单位"从日期换成状态/数值怎么办？** A: 套路不变，先过滤/标记成 0/1，再分段。
- **Q: 双 row_number 差值为什么能分组？** A: win 行之间若被 lose 隔断，`rn` 与 `rn2` 的增速不同步，差值跳变——跳变点即新连胜段起点。

</details>

<!-- APPEND -->
