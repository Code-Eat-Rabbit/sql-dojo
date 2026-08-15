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

---

## 组2 开窗函数 lead/lag

---

### Q4. 波峰波谷 `★★★☆☆` `lead` `lag` `波峰波谷`

> 来源：项目题号 `02_01`　表：`stock_price`

**表结构：**

| id (INTEGER) | ds (TEXT) | price (FLOAT) |
|---|---|---|
| 1 | 2024-01-01 | 10.0 |
| 1 | 2024-01-02 | 12.5 |
| 1 | 2024-01-03 | 11.0 |

给定股票/商品价格时间序列表 `stock_price(id, ds, price)`，标记每个时间点是「波峰」还是「波谷」。
波峰：价格大于前一天和后一天；波谷反之。

*提示：lag 看前一天，lead 看后一天，用 case when 判断。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：经典的「前后值比较」套路——用 LAG 取前一天价格、LEAD 取后一天价格，再用 CASE WHEN 判断当前价格是否同时大于/小于前后值。必须包一层子查询先算出前后值，外层再做 CASE 判断。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 步骤二：外层根据前后值判断波峰波谷
SELECT id, ds, price,
       CASE WHEN price > lag_price AND price > lead_price THEN '波峰'
            WHEN price < lag_price AND price < lead_price THEN '波谷'
            ELSE '持平' END AS type
FROM (
    -- 步骤一：内层用 lag/lead 取前后价格
    SELECT id, ds, price,
           LAG(price) OVER (PARTITION BY id ORDER BY ds) AS lag_price,
           LEAD(price) OVER (PARTITION BY id ORDER BY ds) AS lead_price
    FROM stock_price
) t;
```

**3. 关键解析**：

- 必须包一层子查询再外层 `CASE WHEN`：虽然部分引擎允许在 CASE 里直接嵌套窗口函数，但包一层子查询是最稳定的写法，可读性也更好。
- `PARTITION BY id` 按股票/商品分组，避免跨品种比较；`ORDER BY ds` 保证时间序列顺序。

**4. 知识点延伸**：

**LAG / LEAD 基础语法（吸收 02_02：前后列转换）**

```sql
SELECT id, date, value,
       LAG(value) OVER (PARTITION BY id ORDER BY date) AS prev_value,
       LEAD(value) OVER (PARTITION BY id ORDER BY date) AS next_value
FROM data_table;
```

- `LAG(col, n, default)` 三参数：列名、偏移量（默认 1）、越界默认值（默认 NULL）。
- `LEAD(col, n, default)` 同理，向前/向后取值。
- 首行 LAG 为 NULL 的处理：`LAG(price, 1, price)` 用自身值填充，避免 NULL 干扰后续计算。

**5. 面试追问**：

- **Q: 首尾行为 NULL 怎么办？** A: 使用第三参数 default（如 `LAG(price, 1, price)` 用自身填充）或外层 `COALESCE(lag_price, price)`。
- **Q: 相邻两天价格相等算峰吗？** A: 题面使用严格大于/小于（`>` / `<`），相等归入「持平」。实际业务中边界口径需与面试官确认。

</details>

---

### Q5. 变化率计算 `★★★☆☆` `lag` `面试`

> 来源：项目题号 `02_03`　表：`metrics`

**表结构：**

| date (TEXT) | value (INTEGER) |
|---|---|
| 2024-01-01 | 100 |
| 2024-01-02 | 120 |
| 2024-01-03 | 115 |

给定指标表 `metrics(date, value)`，计算每日的环比变化率。

*提示：lag 取前值，计算差值/变化率。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：用 LAG 取前一行的 value，计算 `(当前 - 前值) / 前值 * 100` 即为环比变化率。注意乘 `100.0` 防止整数除法丢失精度。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 面试题典型场景：计算变化率
SELECT date, value,
       LAG(value) OVER (ORDER BY date) AS prev_value,
       ROUND((value - LAG(value) OVER (ORDER BY date)) * 100.0
             / LAG(value) OVER (ORDER BY date), 2) AS change_pct
FROM metrics;
```

**3. 关键解析**：

- `* 100.0` 是关键：SQL 中两个整数相除会截断小数部分（如 `20 / 100 = 0`），乘以 `100.0` 将表达式提升为浮点运算。
- `ROUND(..., 2)` 保留两位小数，便于阅读。
- 同一个 `LAG(value) OVER (ORDER BY date)` 写了三次，引擎只计算一次（优化器去重）。

**4. 知识点延伸**：

- **环比 vs 同比口径**：环比 = 与上一期比（月环比、周环比）；同比 = 与去年同期比（如今年 1 月 vs 去年 1 月）。同比需在 PARTITION BY 中引入年份维度。
- **首行 NULL 变化率**：第一行没有前值，LAG 返回 NULL，计算结果也为 NULL。业务上可用 `COALESCE(change_pct, 0)` 或直接过滤。

**5. 面试追问**：

- **Q: 前值为 0 怎么办？** A: 必须防除零：`CASE WHEN prev_value = 0 THEN NULL ELSE ROUND((value - prev_value) * 100.0 / prev_value, 2) END`。除零会产生运行时错误或返回 NULL，不可忽略。
- **Q: 环比和同比在 SQL 写法上有什么区别？** A: 同比需要在 PARTITION BY 中加入周期维度（如月份），使 LAG 跨年回溯而非取相邻行。

</details>

---

## 组3 三种排序开窗

---

### Q6. 三种排序开窗：row_number / rank / dense_rank `★★☆☆☆` `row_number` `rank` `dense_rank` `topN`

> 来源：项目题号 `03_01`　表：`scores`

**表结构：**

| student (TEXT) | score (INTEGER) |
|---|---|
| a | 90 |
| b | 90 |
| c | 85 |
| d | 80 |

掌握三种排序开窗函数的区别：

- `row_number()`: 连续编号 1,2,3,4...（不并列）
- `rank()`: 跳号 1,2,2,4...（并列同号，下一个跳号）
- `dense_rank()`: 不跳号 1,2,2,3...（并列同号，下一个不跳）

*提示：row_number: 1,2,3,4 严格递增；rank: 1,2,2,4 跳跃；dense_rank: 1,2,2,3 不跳跃。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：同一张表上同时调用三个排序函数，直观对比输出差异。理解并列场景下各函数的行为是面试高频考点。

**2. 参考 SQL（Hive 方言）**：

```sql
SELECT student, score,
       ROW_NUMBER() OVER (ORDER BY score DESC) AS rn,
       RANK()       OVER (ORDER BY score DESC) AS rk,
       DENSE_RANK() OVER (ORDER BY score DESC) AS dr
FROM scores;
```

**3. 关键解析**：

- 三个函数共享同一个 `OVER (ORDER BY score DESC)`，区别仅在于并列时的编号策略。

**三函数输出对照表（示例数据含并列）**：

| student | score | rn (row_number) | rk (rank) | dr (dense_rank) |
|---|---|---|---|---|
| a | 90 | 1 | 1 | 1 |
| b | 90 | 2 | 1 | 1 |
| c | 85 | 3 | 3 | 2 |
| d | 80 | 4 | 4 | 3 |

- `row_number`：并列也分先后（顺序不确定），编号严格 1,2,3,4。
- `rank`：并列同号（a、b 都为 1），下一个跳到 3（没有第 2 名）。
- `dense_rank`：并列同号（a、b 都为 1），下一个紧接为 2（不跳号）。

**4. 知识点延伸**：

**每个学生成绩第二高的科目（吸收 03_02）**

```sql
SELECT student, subject
FROM (
    SELECT student, subject, score,
           DENSE_RANK() OVER (PARTITION BY student ORDER BY score DESC) AS dr
    FROM student_scores
) t
WHERE dr = 2;
```

- `PARTITION BY student` 按学生分组，每个学生内部独立排序。
- 使用 `dense_rank` 而非 `rank` 的原因：如果有并列第一，`rank` 会跳到 3，导致 `WHERE rk = 2` 取不到任何行。`dense_rank` 保证并列后紧接 2，一定能取到第二名。

**5. 面试追问**：

- **Q: TopN 并列时只取一条怎么办？** A: 用 `row_number()`，它不并列，每行编号唯一，`WHERE rn <= N` 严格取 N 条。
- **Q: 取第 N 高为什么推荐 dense_rank？** A: 并列不跳号，第 N 名一定存在。例如取第二名，即使有并列第一，`dense_rank` 的第二名编号仍为 2；而 `rank` 的第二名编号可能跳到 3。

</details>

## 组4 累计汇总

### Q7. 统计每个用户累计访问次数 `★★☆☆☆` `sum` `累计` `聚合开窗`

> 来源：项目题号 `04_01`　表：`user_visits`

**表结构：**

| user_id (INTEGER) | month_id (TEXT) | visit_cnt_1m (INTEGER) |
|---|---|---|
| 1 | 2024-01 | 30 |
| 1 | 2024-02 | 25 |
| 2 | 2024-01 | 15 |

用聚合开窗函数 `sum() over()` 统计每个用户按月累计访问次数。

*提示：sum(col) over(partition by ... order by ...) 实现累计；不加 order by 则是全局总和。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：经典的「累计求和」套路——`SUM() OVER(PARTITION BY ... ORDER BY ...)` 是聚合开窗函数的核心用法，`ORDER BY` 决定了累计方向，`PARTITION BY` 决定了分组粒度。

**2. 参考 SQL（Hive 方言）**：

```sql
SELECT user_id, month_id, visit_cnt_1m,
       SUM(visit_cnt_1m) OVER (PARTITION BY user_id ORDER BY month_id) AS cumulative_visits
FROM user_visits;
```

**3. 关键解析**：

- **加 `ORDER BY` = 累计值**：`SUM(col) OVER(PARTITION BY user_id ORDER BY month_id)` 会按 `month_id` 顺序逐行累加，得到每个用户截至当月的累计访问次数。
- **不加 `ORDER BY` = 组内总量**：去掉 `ORDER BY month_id` 后，`SUM(col) OVER(PARTITION BY user_id)` 计算的是该用户的**全局总和**（所有月份加总），同一用户每行值相同。

```sql
-- 对照：不加 ORDER BY → 组内总量（每行值相同）
SELECT user_id, month_id, visit_cnt_1m,
       SUM(visit_cnt_1m) OVER (PARTITION BY user_id) AS total_visits
FROM user_visits;
```

| user_id | month_id | visit_cnt_1m | cumulative_visits（加 ORDER BY） | total_visits（不加 ORDER BY） |
|---|---|---|---|---|
| 1 | 2024-01 | 30 | 30 | 55 |
| 1 | 2024-02 | 25 | 55 | 55 |
| 1 | 2024-03 | 20 | 75 | 55 |

**4. 知识点延伸**：

**滚动最小值求历史新低（吸收 04_08：历史新低的商品）**

`MIN(price) OVER(PARTITION BY id ORDER BY ds)` 实现滚动最小值，用于判断当天价格是否为历史新低。

> **勘误框**：manifest 原答案（04_08）中 `LAG(price) OVER(...)` 写在 `WHERE` 里是**非法语法**——窗口函数不能出现在 `WHERE` 子句中（SQL 执行顺序：`WHERE` 先于 `SELECT` 中的窗口计算）。正确做法是先在 CTE 中算好 `min_so_far` 与 `prev_price`，再在外层过滤。

```sql
-- 正确写法：CTE 先算窗口函数，外层再过滤
WITH marked AS (
    SELECT id, ds, price,
           MIN(price) OVER (PARTITION BY id ORDER BY ds) AS min_so_far,
           LAG(price)  OVER (PARTITION BY id ORDER BY ds) AS prev_price
    FROM product_price
)
SELECT id, ds, price
FROM marked
WHERE price = min_so_far        -- 当前价格 = 历史最低
  AND prev_price IS NOT NULL    -- 排除首日（无历史可比）
  AND price < prev_price;       -- 严格新低（比前一天还低）
```

**5. 面试追问**：

- **Q: ROWS 与 RANGE 帧的区别？** A: `ROWS` 按物理行偏移定义帧范围（如 `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`），`RANGE` 按排序值的逻辑距离定义（排序值相同的行在同一帧）。默认帧在加 `ORDER BY` 时为 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`。
- **Q: 窗口函数能写进 WHERE 吗？** A: 不能。SQL 执行顺序为 `FROM → WHERE → GROUP BY → HAVING → SELECT`，窗口函数在 `SELECT` 阶段计算，`WHERE` 先于窗口函数执行。解决办法：用 CTE 或子查询先把窗口函数算出来，再在外层 `WHERE` 过滤。

</details>

---

### Q8. 同时在线人数 `★★★☆☆` `同时在线` `进出时间` `累加`

> 来源：项目题号 `04_02`　表：`live_log`

**表结构：**

| room_id (INTEGER) | user_id (INTEGER) | login_time (TEXT) | logout_time (TEXT) |
|---|---|---|---|
| 101 | 1 | 2021-03-10 08:00:00 | 2021-03-10 09:30:00 |
| 101 | 2 | 2021-03-10 08:30:00 | 2021-03-10 10:00:00 |

给定用户进入和离开直播间的时间，计算同时在线人数峰值。
核心技巧：进入 +1，离开 -1，按时间排序累加。

*提示：进入+1，离开-1，按时间排序累加；用 union all 把进出事件合并。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：经典的「区间转事件流」套路——把用户在线的 `[login_time, logout_time]` 区间拆成两个事件点：进入 = +1，离开 = -1。合并后按时间排序做累计求和，累计值的最大值即为峰值在线人数。核心抽象：把「区间问题」转成「事件流问题」。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 步骤一：进入+1，离开-1，合并为事件流
WITH events AS (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE substr(login_time, 1, 10) = '2021-03-10'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE substr(logout_time, 1, 10) = '2021-03-10'
),
-- 步骤二：按时间排序累加，得到每个时刻的在线人数
cumulative AS (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM events
)
-- 步骤三：取每个房间的最大值
SELECT room_id, MAX(online_cnt) AS max_online
FROM cumulative
GROUP BY room_id;
```

**3. 关键解析**：

- `UNION ALL` 而非 `UNION`：进出事件是独立事件，即使值相同也不能去重，否则会丢失事件导致计算错误。
- `SUM(user_type) OVER(PARTITION BY room_id ORDER BY event_time)`：`ORDER BY` 让 SUM 从「全局总和」变为「逐行累加」，这正是同时在线人数的计算方式。

**4. 知识点延伸**：

**每小时峰值（吸收 04_03）**：在步骤二的累计结果上，按小时粒度分组取最大值。

```sql
WITH events AS (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE substr(login_time, 1, 10) = '2021-03-10'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE substr(logout_time, 1, 10) = '2021-03-10'
),
cumulative AS (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM events
)
SELECT room_id, substr(event_time, 1, 13) AS hour_slot, MAX(online_cnt) AS max_online
FROM cumulative
GROUP BY room_id, substr(event_time, 1, 13);
```

- `substr(event_time, 1, 13)` 取 `yyyy-mm-dd HH` 截取到小时粒度。

**不限时段（吸收 04_04）**：去掉步骤一的日期 WHERE 筛选，计算有史以来每小时最大同时在线人数。

```sql
WITH events AS (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
),
cumulative AS (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM events
)
SELECT room_id, substr(event_time, 1, 13) AS hour_slot, MAX(online_cnt) AS max_online
FROM cumulative
GROUP BY room_id, substr(event_time, 1, 13);
```

**峰值时间（吸收 04_05）**：不仅求峰值人数，还要输出达到峰值的时间点。用 `RANK()` 取每个房间在线人数最高的那一行。

```sql
WITH events AS (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE substr(login_time, 1, 10) = '2022-05-01'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE substr(logout_time, 1, 10) = '2022-05-01'
),
cumulative AS (
    -- 关键细节：order by event_time, user_type
    -- user_type = -1（离开）排在 +1（进入）前面
    -- 同一时刻"先出后进"的保守口径，避免峰值虚高
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
```

- `ORDER BY event_time, user_type`：`user_type` 的 -1 排在 +1 前面（升序）。当同一时刻有人进、有人出时，先处理 -1（离开）再处理 +1（进入），这是「保守口径」——峰值不会因为同一秒进出叠加而虚高。

**5. 面试追问**：

- **Q: 用 UNION 还是 UNION ALL？** A: `UNION ALL`。进出事件是独立语义，即使拼接后出现完全相同的行也不能去重。`UNION` 会去重，导致丢失事件、峰值计算偏低。
- **Q: 同一秒有人进有人出算几个在线？** A: 口径问题。保守口径是先处理 -1 再处理 +1（峰值不虚高），通过 `ORDER BY event_time, user_type` 实现。激进口径则反过来。实际面试中说明口径即可。

</details>

---

### Q9. 求最小达到某累计金额的日期 `★★★★★` `美团`

> 来源：项目题号 `04_06`　表：`user_spend`

**表结构：**

| user_id (INTEGER) | dt (TEXT) | price (REAL) |
|---|---|---|
| 1 | 2024-01-01 | 300 |
| 1 | 2024-01-02 | 500 |
| 1 | 2024-01-03 | 400 |

给定每个用户每天的消费金额，求每个用户累计消费首次达到 1000 元的日期。

*提示：先累加，再 where 筛选，最后 min 取最早日期。*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：累计求和 → 筛选达标行 → 取最早日期，三步走。先用 `SUM() OVER()` 算出每个用户每天的累计消费，再筛选 `cum_price >= 1000` 的行，最后 `MIN(dt)` 取首次达标日期。

**2. 参考 SQL（Hive 方言）**：

```sql
WITH cumulative AS (
    SELECT user_id, dt, price,
           SUM(price) OVER (PARTITION BY user_id ORDER BY dt) AS cum_price
    FROM user_spend
)
SELECT user_id, MIN(dt) AS reach_date
FROM cumulative
WHERE cum_price >= 1000
GROUP BY user_id;
```

**3. 关键解析**：

- 累计消费使用 `SUM(price) OVER(PARTITION BY user_id ORDER BY dt)` 实现逐日累加。
- 达标后可能持续达标（比如 1 月 3 日达标后 1 月 4 日仍然 >= 1000），所以需要 `MIN(dt)` 取最早的那一天。
- `WHERE cum_price >= 1000` 在外层过滤，而非在 CTE 内部，因为窗口函数不能出现在 WHERE 中。

**4. 知识点延伸**：

**商品复购（吸收 04_07）**：计算每个用户购买了 >= 2 次的商品。

```sql
SELECT user_id, product_id
FROM orders
GROUP BY user_id, product_id
HAVING COUNT(DISTINCT order_id) >= 2;
```

- `HAVING` 过滤聚合后的组（WHERE 过滤聚合前的行）。
- 使用 `COUNT(DISTINCT order_id)` 而非 `COUNT(*)`：如果一个订单包含多行（如一个订单买多个商品），`COUNT(*)` 会把同一订单的多行都算进去，`COUNT(DISTINCT order_id)` 保证按订单去重。在本项目中 `orders` 表一行对应一条商品记录，但面试中口径题常见，用 `DISTINCT` 更稳健。

**5. 面试追问**：

- **Q: 为什么 MIN(dt) 还要 GROUP BY user_id？** A: 达标后可能持续达标（后续每天累计值都 >= 1000），`WHERE cum_price >= 1000` 会返回多行，需要 `GROUP BY user_id` 配合 `MIN(dt)` 取每个用户的最早达标日期。
- **Q: HAVING 和 WHERE 的执行时机？** A: `WHERE` 在聚合前过滤行（`GROUP BY` 之前），`HAVING` 在聚合后过滤组（`GROUP BY` 之后）。窗口函数不能用 WHERE 过滤，需 CTE / 子查询先算再过滤。

</details>

---

<!-- APPEND -->
