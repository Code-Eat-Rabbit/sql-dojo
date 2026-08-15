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
| 季度 | `concat(substr(date,1,4), 'Q', cast((month(date)-1) div 3+1 as string))` | 公式 `(m-1) div 3+1` 必会手写；Hive 整除用 div |
| 半年 | 同上，`(m-1) div 6+1` | |
| 年月 | `substr(date, 1, 7)` 或 `date_format(date,'yyyy-MM')` | |
| 日期差 | `datediff(a, b)`（a-b 天数） | Q2 |
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
6. **Hive 与标准 SQL 差异**：`date_add(d, n)` 不是 `INTERVAL` 语法；`/` 恒返回 double，整除用 `div`；多参取小用 `least()`（SQLite 是 `min()`）；`collect_list/collect_set` vs `group_concat`；`get_json_object` vs `json_extract`。
7. **什么时候用递归 CTE，什么时候用开窗**：先看能否用 `row_number/lag + 聚合开窗` 的"分段子问题"套路解决（连续、分段、层级汇总大多可以）；真需要逐行传递状态（如逐行 forward fill、树遍历）才用递归——面试先答开窗解法是加分项（源自题 10_01 的辨析）。

# Part 2 精选题册

## 组1 连续问题

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

- 方法 2 用 `LAG(date, 1)` 和 `LAG(date, 2)` 取前两天，两个 `DATEDIFF` 全为 1 即连续三天。前两行 prev1/prev2 为 NULL 时 `DATEDIFF(date, NULL)` 结果为 NULL、不满足 `= 1` 自动排除，无需特殊处理。
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
-- 解法1：双 row_number 差值法（修正版）
WITH numbered AS (
    SELECT user_id, date, result,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) AS rn,
           ROW_NUMBER() OVER (PARTITION BY user_id, result ORDER BY date) AS rn2
    FROM games                      -- 注意：不能在这里过滤 win！
)
SELECT user_id, MAX(streak) AS max_streak
FROM (
    SELECT user_id, rn - rn2 AS grp, COUNT(*) AS streak
    FROM numbered
    WHERE result = 'win'            -- 过滤放在窗口计算之后
    GROUP BY user_id, grp
) t
GROUP BY user_id;
```

> **勘误框**：manifest 原答案将 `WHERE result='win'` 放在 CTE 内部，导致窗口函数只看到 win 行，`PARTITION BY user_id, result` 退化为 `PARTITION BY user_id`，rn 与 rn2 恒相等、差值恒 0，所有 win 行被并为同一组——连胜数变成了总胜场（实测 `win,win,lose,win,win` 返回 4 而非正确答案 2）。
>
> 正确机制：rn 基于**全部行**编号（含 lose），rn2 基于 `user_id, result` 分区后只对 win 行编号；连续 win 段内两序号同步递增、差值恒定，被 lose 隔断后 rn 继续递增而 rn2 重置、差值跳变——这才是分组的来源。因此 `WHERE result='win'` 必须放在窗口计算之后。

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

- 解法 1 中 `rn` 基于**全部行**编号（含 lose），`rn2` 基于 `user_id, result` 分区后只对 win 行编号。连续 win 段内两者同步递增、差值恒定；被 lose 隔断后 rn 继续递增而 rn2 重置、差值跳变——形成新分组。关键：`WHERE result='win'` 必须在窗口计算之后，否则 CTE 只看到 win 行，rn 与 rn2 退化相等。
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
- **Q: 双 row_number 差值为什么能分组？** A: win 行之间若被 lose 隔断，`rn`（全局序）继续递增而 `rn2`（win 行内序）重置，差值跳变——跳变点即新连胜段起点。注意 `WHERE result='win'` 必须在窗口计算之后，否则 CTE 只含 win 行，两个分区退化等价，差值恒 0。

</details>

---

## 组2 开窗函数 lead/lag

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

- `* 100.0` 是关键：整数相除截断是 SQLite/Postgres 等引擎的行为（本项目本地 SQLite 即如此，如 `20 / 100 = 0`）；Hive 的 `/` 恒返回 double，无此问题。但 `*100.0` 写法跨方言稳健、无害，保留是好习惯。
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

## 组5 区间与 NULL

### Q10. 区间交集 — 合并区间 `★★★★☆` `区间` `合并`

> 来源：项目题号 `05_01`　表：`raw_intervals`

| start | end |
|-------|-----|
| 1     | 3   |
| 2     | 5   |
| 8     | 10  |

给定多个区间（start, end），合并所有有交集的区间。

*提示：用 max(end) over() 滚动获取之前的最大 end，start > 之前的 max_end 则开启新区间*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：经典区间合并——按 start 排序后，用滚动最大值判断当前区间是否与前面所有已处理区间重叠，不重叠则开启新组，最终按组取 min(start) 和 max(end)。

**2. 参考 SQL（Hive 方言）**：

```sql
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
```

**3. 关键解析**：

- **为什么用 `MAX(end) OVER(...前置行)` 而不是 `LAG(end)`**：`LAG(end)` 只看上一行的 end，但如果前面的区间很长（比如第 1 行是 [1,10]，第 3 行是 [5,6]），只看上一行会误判。滚动最大值 `MAX(end)` 能覆盖之前所有行的最大端点，确保不遗漏任何重叠。
- **帧 `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING`**：从第一行到当前行的前一行，**排除当前行自身**。因为当前行的 end 不应参与"之前区间"的判断——我们要比较的是当前 start 与**之前所有区间**的 max end。
- **`SUM(new_group) OVER(ORDER BY start)` 累加组号**：每个 `new_group=1` 的位置就是新组的起点，累加后同一组的行共享相同的 `group_id`，外层按组聚合即可得到合并后的区间。

**4. 知识点延伸**：

**与 Q3 延伸（01_06 lag 断点法）的对比**：Q3 延伸中用 `LAG(time) = session_end` 判断会话断点，前提是数据**无重叠**——每条记录只与前一条比较。而本题涉及**有重叠、甚至嵌套**的区间，`LAG` 只看紧邻上一行会漏掉更早的长区间，必须用滚动 `MAX(end)` 覆盖全部前置行。结论：无重叠场景 `LAG` 够用；有重叠或嵌套必须滚动 `MAX`。

**5. 面试追问**：

- **Q: 区间是日期不是数字怎么办？** A: 用 `DATEDIFF` 转为数值差比较，或直接比较日期大小（日期类型天然支持 `>`/`<`），窗口函数的套路完全不变，只是数据类型从整数换成日期。
- **Q: 首行的 max_end_so_far 是 NULL，CASE 怎么走？** A: 首行的帧 `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` 为空集，`MAX(end)` 返回 NULL。此时 `start > NULL` 的结果是 NULL（UNKNOWN），SQL 的 CASE 将 NULL 视为非 TRUE，走 ELSE 分支返回 0。因此首行 `new_group=0`，累加后 `group_id=0`，天然归入第一组——行为正确。这是 SQL 三值逻辑（TRUE/FALSE/UNKNOWN）的一个隐式依赖，面试中讲清楚"UNKNOWN → ELSE"这个走向即可。

</details>

---

### Q11. 填补缺失值 `★★★☆☆` `缺失值` `lag` `填充`

> 来源：项目题号 `09_02`　表：`data_table`

| id | date       | value |
|----|------------|-------|
| 1  | 2024-01-01 | 10    |
| 1  | 2024-01-02 | NULL  |
| 1  | 2024-01-03 | NULL  |
| 1  | 2024-01-04 | 20    |

用上一个非空值填充缺失值（forward fill）。

*提示：窗口函数 CASE+MAX 取最近非空日期再自关联，或相关子查询取"最近的非空前值"*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：对每一行，如果当前 value 为 NULL，就用同一 id 中最近一条非 NULL 记录的 value 填充。窗口函数解法：用 `CASE + MAX() OVER` 标记"最近非空日期"，再自关联回原表取值——与 Q3 的"断点标记+累加分段"同宗。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 窗口函数版：CASE 造非空日期 + MAX 累计开窗取最近一次非空出现位置
WITH marked AS (
    SELECT id, date, value,
           MAX(CASE WHEN value IS NOT NULL THEN date END)
               OVER (PARTITION BY id ORDER BY date
                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS last_nn_date
    FROM data_table
)
SELECT m.id, m.date, m.value,
       t.value AS filled_value
FROM marked m
LEFT JOIN data_table t
  ON t.id = m.id AND t.date = m.last_nn_date;
```

> **SQLite/本地练习写法**（相关子查询版，O(n^2) 性能，部分 Hive 版本不支持子查询内 LIMIT）：
> ```sql
> WITH filled AS (
>     SELECT id, date, value,
>            CASE WHEN value IS NOT NULL THEN value
>                 ELSE (SELECT t2.value FROM data_table t2
>                       WHERE t2.id = t1.id AND t2.date < t1.date AND t2.value IS NOT NULL
>                       ORDER BY t2.date DESC LIMIT 1)
>            END AS filled_value
>     FROM data_table t1
> )
> SELECT * FROM filled;
> ```

**3. 关键解析**：

- **`MAX(CASE WHEN value IS NOT NULL THEN date END) OVER(...)`**：核心技巧——CASE 将 NULL 值的位置填为 NULL（不参与 MAX），非 NULL 值的位置保留日期，MAX 累计开窗取到截至当前行的最近一个非 NULL 日期。这是"标记最近非空日期"的标准写法。
- **自关联取值**：拿到 `last_nn_date` 后，LEFT JOIN 回原表取出该日期的 value——因为非 NULL 行的 `last_nn_date = date`，所以自身匹配；NULL 行匹配到最近的非 NULL 行。
- **相关子查询版（备注块）**的时间复杂度为 O(n^2)，外层 n 行每行触发一次子查询扫描。窗口函数版 O(n)，是生产环境的首选。

**4. 知识点延伸**：

**状态标记（吸收 09_01）**：给定状态变更日志，用 `LEAD` 给每个状态区间补上终点。

```sql
SELECT id, status, start_time,
       LEAD(start_time) OVER (PARTITION BY id ORDER BY start_time) AS end_time
FROM status_log;
```

- `LEAD(start_time)` 取同一 id 下按 start_time 排序的下一行时间，作为当前状态的结束时刻。最后一个状态的 end_time 为 NULL（表示持续到当前）。

**5. 面试追问**：

- **Q: forward fill 的窗口函数解法？** A: `LAST_VALUE(value IGNORE NULLS) OVER(PARTITION BY id ORDER BY date)` —— `IGNORE NULLS` 让窗口跳过 NULL 值取最近一个非 NULL。但各引擎支持差异大：Oracle、Snowflake 支持 `IGNORE NULLS`；Hive 的 `LAST_VALUE` **不忽略 NULL**，需用 `CASE + MAX` 技巧或递归 CTE 替代。面试中答出"标准写法 + 引擎差异 + 替代方案"即可。
- **Q: 相关子查询为什么慢？** A: 相关子查询对外层每一行都独立执行一次内层查询，无法利用批量优化（索引嵌套循环或哈希连接），复杂度 O(n²)。窗口函数方案一次扫描完成，复杂度 O(n)，但需引擎支持 `IGNORE NULLS` 等特性。实际选择取决于数据规模和引擎能力。

</details>

---

## 组6 关联应用

### Q12. 每一门课大于60分的学生的所有科目成绩 `★★★☆☆` `子查询` `join` `关联`

> 来源：项目题号 `06_01`　表：`student`、`sc`、`class`

**表结构：**

**student**

| id (INTEGER) | student_name (TEXT) |
|---|---|
| 1 | 张三 |
| 5 | 钱七 |

**sc**

| sid (INTEGER) | cid (INTEGER) | score (REAL) |
|---|---|---|
| 1 | 1 | 88.0 |
| 5 | 3 | 72.0 |

**class**

| id (INTEGER) | class_name (TEXT) |
|---|---|
| 1 | 语文 |
| 3 | 英语 |

查询「所有科目都大于 60 分」的学生的全部成绩记录。

*提示：NOT IN 排除有不及格科目的学生，再用 JOIN 查出这些学生全部科目和成绩*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：全称量词的经典转化——"所有科目都 >60"等价于"不存在任何一门 <=60"。用 NOT IN 子查询排除有不及格记录的学生 id，再 JOIN 回 student、class、sc 三表取全部成绩明细。

**2. 参考 SQL（Hive 方言）**：

```sql
SELECT t0.student_name, t2.class_name, t1.score
FROM student t0
JOIN sc t1 ON t0.id = t1.sid
JOIN class t2 ON t1.cid = t2.id
WHERE t0.id NOT IN (
    SELECT sid FROM sc WHERE score <= 60
);
```

**3. 关键解析**：

- **双重否定思想**：SQL 没有"FOR ALL"量词，用 `NOT IN (存在 <=60 的 sid)` 实现"所有科目都 >60"——全称量词转化为对补集的否定，这是关系除法的基础思路。
- 三表 JOIN 顺序：student → sc（按 id = sid）→ class（按 cid = id），最后用 WHERE 过滤合格学生。

**4. 知识点延伸**：

**聚合解法（group by + having）**：另一种思路是先按学生分组，`HAVING MIN(score) > 60` 筛选出每科都及格的学生，再 JOIN 回明细表拿全部记录：

```sql
SELECT s.student_name, c.class_name, sc.score
FROM student s
JOIN sc ON s.id = sc.sid
JOIN class c ON sc.cid = c.id
WHERE s.id IN (
    SELECT sid FROM sc GROUP BY sid HAVING MIN(score) > 60
);
```

**NOT IN 的 NULL 陷阱**：如果子查询 `SELECT sid FROM sc WHERE score <= 60` 返回的 sid 集合中包含 NULL，则 `NOT IN` 整体返回空集——因为 `x NOT IN (a, NULL, b)` 等价于 `x <> a AND x <> NULL AND x <> b`，而 `x <> NULL` 恒为 UNKNOWN，整个 AND 链结果恒不为 TRUE（某比较为 FALSE 时整链为 FALSE，某比较为 UNKNOWN 时整链为 UNKNOWN），WHERE 过滤掉所有行。安全替代写法用 `NOT EXISTS`：

```sql
SELECT t0.student_name, t2.class_name, t1.score
FROM student t0
JOIN sc t1 ON t0.id = t1.sid
JOIN class t2 ON t1.cid = t2.id
WHERE NOT EXISTS (
    SELECT 1 FROM sc t3
    WHERE t3.sid = t0.id AND t3.score <= 60
);
```

**5. 面试追问**：

- **Q: NOT IN 子查询里有 NULL 会怎样？** A: 返回空集。`NOT IN` 底层展开为 `<> AND <> AND ...`，只要集合中有 NULL，就会产生一个 `<> NULL` 恒为 UNKNOWN 的条件，导致整个 AND 表达式恒不为 TRUE（WHERE 只保留 TRUE 的行），所有行被过滤。改用 `NOT EXISTS` 或 `NOT IN (SELECT ... WHERE col IS NOT NULL)` 可规避。
- **Q: "存在一门 >60"和"所有科目 >60"的 SQL 写法差异？** A: "存在"直接用 `WHERE sid IN (SELECT sid FROM sc WHERE score > 60)`；"所有"需要双重否定——`NOT IN (SELECT sid FROM sc WHERE score <= 60)` 或聚合解法 `GROUP BY sid HAVING MIN(score) > 60`。前者是存在量词，后者是全称量词，SQL 处理方式完全不同。

</details>

---

### Q13. 相互关注（共同好友） `★★★☆☆` `自关联` `join` `相互关注`

> 来源：项目题号 `06_02`　表：`fans`

**表结构：**

**fans**

| from_user (TEXT) | to_user (TEXT) |
|---|---|
| alice | bob |
| bob | alice |
| alice | charlie |

在关注关系表 `fans(from_user, to_user)` 中，找出相互关注的用户对。

*提示：方法1 用自关联 a 关注 b 且 b 关注 a，方法2 用 union 后 group by having count >= 2*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：相互关注 = A 关注 B 且 B 关注 A。两种思路：自关联（JOIN 自身，交换 from/to 匹配）或合并去重（双向 UNION ALL 后按对分组计数）。无论哪种，都需要去重避免 (A,B) 和 (B,A) 同时出现。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 方法1：自关联 JOIN
SELECT a.from_user AS u1, a.to_user AS u2
FROM fans a
JOIN fans b ON a.from_user = b.to_user AND a.to_user = b.from_user
WHERE a.from_user < a.to_user;

-- 方法2：UNION ALL + GROUP BY
SELECT u1, u2 FROM (
    SELECT from_user AS u1, to_user AS u2 FROM fans
    UNION ALL
    SELECT to_user AS u1, from_user AS u2 FROM fans
) t
GROUP BY u1, u2
HAVING COUNT(*) >= 2;
```

**3. 关键解析**：

- **方法 1 的 `a.from_user < a.to_user`**：自关联会同时匹配 (alice,bob) 和 (bob,alice) 两行，加 `<` 条件只保留字典序较小的排列，实现无向对去重。
- **方法 2 的 UNION ALL 双向展开**：将每条关注关系正反各写一次，相互关注的对会出现两次（正 + 反），单向关注的只出现一次。`HAVING COUNT(*) >= 2` 筛出出现 >=2 次的即为互关对。

**4. 知识点延伸**：

**千亿级数据优化（吸收 06_03）**：当数据量达到千亿级别时，普通 JOIN 会触发全量 shuffle（数据在节点间重分布），代价极高。核心优化策略：

1. **Map-Side Join（小表广播 / MapJoin）**：如果其中一张表足够小，将其广播到所有 Map 节点内存中，在 Map 阶段直接完成连接，完全避免 Shuffle。Hive 中用 `/*+ MAPJOIN(小表别名) */` 提示或设置 `hive.auto.convert.join=true`（自动将小表转为 MapJoin）。
2. **分桶表（Bucket）**：按用户 ID 对两张表做相同数量的分桶（CLUSTERED BY user_id INTO N BUCKETS），保证相同键的数据落在同一节点。JOIN 时只做同桶连接，数据量降为原来的 1/N。
3. **Bloom Filter 预过滤**：对一张表的键构建 Bloom Filter，先过滤另一张表中"不可能匹配"的行，大幅减少参与 JOIN 的数据量。部分引擎（如 Spark）内置 Bloom Filter Join 优化；Hive 中可通过在 ETL 层预过滤不可能相互关注的键来近似实现（如先按各自活跃度做内层过滤，缩小 JOIN 输入规模）。
4. **核心原则**：避免全量 Shuffle JOIN。Shuffle 是分布式计算中最昂贵的操作（全量数据网络传输 + 磁盘写），优先用上述手段将 JOIN 下推到 Map 端或缩小数据规模。

**5. 面试追问**：

- **Q: 为什么 WHERE 里加 `<` 比较？** A: 无向对去重。自关联 JOIN 会同时产生 (alice,bob) 和 (bob,alice) 两条结果，加 `a.from_user < a.to_user` 只保留字典序较小的那条，保证每对只出现一次。
- **Q: 相互关注和"共同好友"区别？** A: 相互关注是二元关系判定——给定关系表，判断 A↔B 是否双向成立；共同好友是三元关系——给定关系表，找 A 和 B 共同关注的所有用户 C。后者需要找交集：A 关注的集合 ∩ B 关注的集合，SQL 写法为 `WHERE A.to_user = B.to_user AND A.from_user = '目标用户1' AND B.from_user = '目标用户2'`。两者底层都是 JOIN，但语义和输出维度不同。

</details>

---

## 组7 留存计算

### Q14. 七日留存计算 `★★★☆☆` `留存` `retention`

> 来源：项目题号 `07_01`　表：`user_active`

| user_id | date       |
|---------|------------|
| 1       | 2024-01-01 |
| 1       | 2024-01-08 |
| 2       | 2024-01-01 |

给定用户每日活跃表，计算七日留存率（Day0 活跃的用户在 Day7 仍然活跃的比例）。

*提示：先找每个用户的首次活跃日期，再 left join 7 天后的活跃记录，计算比例*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：留存计算的套路——先确定分母（首活用户），再关联留存日的活跃记录，最后用 distinct count 防止重复活跃灌水比例。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 步骤1：找出每个用户的首次活跃日期（分母）
-- 步骤2：left join 第7天活跃记录（保分母，未留存用户不会丢失）
-- 步骤3：count distinct 计算留存率
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
  ON a.user_id = b.user_id
  AND b.date = date_add(a.first_date, 7)
GROUP BY a.first_date;
```

**3. 关键解析**：

- **`MIN(date) 定分母**：留存率的分母是"首次活跃"用户，而非所有活跃用户。用 `MIN(date)` 取每个用户最早出现的日期，确保只看新用户的留存表现。
- **`LEFT JOIN` 保分母**：如果用 `INNER JOIN`，第 7 天没有活跃的用户会被直接丢弃，分母变小、留存率虚高。`LEFT JOIN` 保留所有首活用户，未留存用户的 `b.user_id` 为 NULL，`COUNT(DISTINCT b.user_id)` 自动忽略 NULL。
- **`COUNT(DISTINCT)` 防灌水**：同一用户在第 7 天可能活跃多次（如多次打开 App），`COUNT(DISTINCT b.user_id)` 保证每个人只算一次。

**4. 知识点延伸**：

**留存家族口径表**：不同留存周期的计算逻辑完全一致，只需修改 `date_add` 的偏移天数：

| 留存类型   | 偏移天数 | date_add 参数  |
|-----------|---------|----------------|
| 次日留存   | 1       | `date_add(first_date, 1)`   |
| 3 日留存   | 3       | `date_add(first_date, 3)`   |
| 7 日留存   | 7       | `date_add(first_date, 7)`   |
| 30 日留存  | 30      | `date_add(first_date, 30)`  |

**新增用户口径 vs 活跃用户口径**：本题属于"新增用户口径"——分母限定为用户的首次活跃（`MIN(date)`）。如果是"活跃用户口径"（如：本周活跃的用户下周是否还活跃），分母则是某一周期内的所有活跃用户，不限定首次。两种口径的业务含义不同，面试时要问清楚。

**5. 面试追问**：

- **Q: 为什么用 LEFT JOIN 而不是 INNER JOIN？** A: 分母必须完整。INNER JOIN 会把第 7 天未活跃的用户从结果中剔除，导致分母只包含留存用户，算出的留存率恒为 100%。LEFT JOIN 保留所有首活用户，未留存的 `b.user_id` 为 NULL，正确反映真实留存率。
- **Q: 用户第 7 天活跃多次算几次？** A: `COUNT(DISTINCT b.user_id)` 保证每个用户只算一次。如果用 `COUNT(b.user_id)`（不加 DISTINCT），同一天多次活跃的用户会被重复计算，虚高留存人数。

> 📌 SQLite 等价写法：将 `date_add(a.first_date, 7)` 替换为 `DATE(a.first_date, '+7 days')`，其余逻辑完全相同。

</details>

---

## 组8 数据展开收缩与日期/JSON

### Q15. 数据展开（行转列） `★★☆☆☆` `展开` `行转列`

> 来源：项目题号 `08_01`　表：`user_tags`

| user_id | tags  |
|---------|-------|
| 1       | a,b,c |
| 2       | x,y   |

给定一个用户和其标签列表（逗号分隔），把标签展开为多行。

*提示：用 lateral view explode 把逗号分隔的字符串炸开成多行*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：行转列的核心是将一个单元格内的多值拆成多行。Hive 中直接用 `SPLIT` + `EXPLODE` 一步到位，`LATERAL VIEW` 负责将炸开的结果与原表行关联。

**2. 参考 SQL（Hive 方言）**：

```sql
-- split 按逗号拆字符串为数组，explode 将数组每个元素炸成一行
-- lateral view 将炸出的行与原表 user_id 关联
SELECT user_id, tag
FROM user_tags
LATERAL VIEW EXPLODE(SPLIT(tags, ',')) t AS tag;
```

**3. 关键解析**：

- **`SPLIT(tags, ',')`**：将逗号分隔的字符串拆成 Hive 数组，如 `'a,b,c'` → `['a','b','c']`。
- **`EXPLODE(arr)`**：表生成函数（UDTF），把数组的每个元素输出为一行。Hive 中 explode 与其他列共存时不能直接出现在 SELECT 列表（需 lateral view；SELECT 仅含单个 explode 时可以）。
- **`LATERAL VIEW ... t AS tag`**：虚拟表别名 `t`，将 explode 的输出命名为 `tag` 列，使其可以像普通列一样引用。

**4. 知识点延伸**：

- **`posexplode`**：带序号的展开，输出两列 `(pos, val)`，pos 从 0 开始。适用于需要保留原始顺序或位置信息的场景。
- **`LATERAL VIEW OUTER`**：如果数组为空（如 tags 为空字符串），普通 `LATERAL VIEW` 会丢弃该行，`LATERAL VIEW OUTER` 则保留该行（explode 输出 NULL）。
- **空字符串过滤**：如果原始 tags 中存在空串（如 `'a,,c'`），split 后会产生空元素。用 `WHERE tag != ''` 或在 split 前用 `regexp_replace(tags, ',+', ',')` 合并连续逗号来清洗。

**5. 面试追问**：

- **Q: explode 和 lateral view 的关系？** A: `explode` 是表生成函数（UDTF），输入一行输出多行，但不能直接与原表列共存。`LATERAL VIEW` 是连接语法，把 UDTF 的输出虚拟成一张表，与主表的每一行做类 CROSS JOIN，使 explode 结果可以和原表列一起查询。
- **Q: tags 中有空串元素怎么处理？** A: split 后产生的空串可以用 `WHERE tag != ''` 过滤；或者在 split 前清洗数据，用 `regexp_replace(tags, ',+', ',')` 合并连续逗号、`trim` 去首尾逗号。

> 📌 SQLite 等价写法：SQLite 没有 explode，需用递归 CTE 逐字符解析：
> ```sql
> WITH RECURSIVE split(user_id, tag, rest) AS (
>     SELECT user_id, '', tags || ','
>     FROM user_tags
>     UNION ALL
>     SELECT user_id,
>            SUBSTR(rest, 1, INSTR(rest, ',') - 1),
>            SUBSTR(rest, INSTR(rest, ',') + 1)
>     FROM split
>     WHERE rest != ''
> )
> SELECT user_id, tag FROM split WHERE tag != '';
> ```

</details>

---

### Q16. 数据收缩（列转行） `★★☆☆☆` `收缩` `列转行` `group_concat`

> 来源：项目题号 `08_02`　表：`user_tag_rows`

| user_id | tag |
|---------|-----|
| 1       | a   |
| 1       | b   |
| 1       | c   |
| 2       | x   |

把多行数据按用户合并为一行（聚合标签）。

*提示：用字符串聚合函数将同一 user_id 的多行 tag 拼接为一个逗号分隔字符串*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：列转行是 Q15 行转列的逆操作——用聚合函数将多行值拼成一个字符串。Hive 用 `COLLECT_LIST` 收集为数组再 `CONCAT_WS` 拼接。

**2. 参考 SQL（Hive 方言）**：

```sql
-- collect_list 收集同一组内的所有 tag 为数组
-- concat_ws 用逗号将数组元素拼接成字符串
SELECT user_id, CONCAT_WS(',', COLLECT_LIST(tag)) AS tags
FROM user_tag_rows
GROUP BY user_id;
```

**3. 关键解析**：

- **`COLLECT_LIST(tag)`**：将同一 `user_id` 下的所有 `tag` 收集成一个 Hive 数组，保留重复值。实践中通常保留输入顺序，但非语义保证。
- **`CONCAT_WS(',', arr)`**：用逗号作为分隔符将数组元素拼接为字符串。`WS` = With Separator。遇 NULL 元素自动跳过（不会导致整个结果变 NULL）。

**4. 知识点延伸**：

- **`collect_list` vs `collect_set`**：`collect_list` 保留重复值和插入顺序；`collect_set` 去重但不保序（底层是 HashSet）。需要去重且保序时，用 `sort_array(collect_set(tag))`（先去重再排序）。
- **聚合内排序 `sort_array`**：`sort_array(collect_list(tag))` 对收集到的数组做字典序排序，可用于保证输出稳定。注意 `sort_array` 是升序，如需降序需加 `reverse()`。
- **`CONCAT_WS` vs `CONCAT`**：`CONCAT_WS` 遇 NULL 跳过该元素，其余正常拼接；`CONCAT` 只要有一个参数为 NULL，整个结果就变 NULL。聚合场景优先用 `CONCAT_WS`。

**5. 面试追问**：

- **Q: 要去重且保序怎么办？** A: `collect_set` 去重但不保序，`collect_list` 保序但不去重。如果业务要求既去重又保序，可以用 `sort_array(collect_set(tag))`（先去重再排序），但排序是字典序而非原始插入序。严格保序去重需要用窗口函数 `ROW_NUMBER() PARTITION BY tag` 先去重再 `collect_list`。
- **Q: `concat_ws` 遇 NULL 怎么处理？** A: `concat_ws` 会自动跳过 NULL 元素，只拼接非 NULL 值。而 `concat` 只要有一个入参是 NULL，整个结果就是 NULL。所以在聚合场景中，`concat_ws` 更安全。

> 📌 SQLite 等价写法：`SELECT user_id, GROUP_CONCAT(tag, ',') AS tags FROM user_tag_rows GROUP BY user_id;`

</details>

---

### Q17. 日期格式汇总 `★★☆☆☆` `日期` `汇总`

> 来源：项目题号 `11_03`　表：`date_table`

| date       |
|------------|
| 2024-03-15 |
| 2024-11-20 |

汇总所有日期格式转换的代码：year, mm, quarter, half, ytm, last\*系列。

*提示：记住 substr + 算术的组合模式*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：日期格式转换的核心模式——用 `SUBSTR` 截取年/月部分，再用整除分桶公式计算季度和半年度。不依赖引擎特定函数，纯字符串+算术实现最大兼容性。

**2. 参考 SQL（Hive 方言）**：

```sql
SELECT date,
       -- 年份
       substr(date, 1, 4)                                        AS yr,
       -- 月份
       substr(date, 6, 2)                                        AS mm,
       -- 季度：yyyyQn，公式 (month-1) div 3 + 1
       concat(substr(date,1,4), 'Q',
              cast((cast(substr(date,6,2) as int)-1) div 3 + 1 as string)) AS qtr,
       -- 半年度：yyyyHn，公式 (month-1) div 6 + 1
       concat(substr(date,1,4), 'H',
              cast((cast(substr(date,6,2) as int)-1) div 6 + 1 as string)) AS half,
       -- 年月：yyyy-MM
       substr(date, 1, 7)                                        AS ytm
FROM date_table;

-- last 系列（滚动窗口）：
-- 最近12个月：WHERE date >= date_sub(current_date, 365)
-- 最近30天 ：WHERE date >= date_sub(current_date, 30)
-- 最近60天 ：WHERE date >= date_sub(current_date, 60)
-- 最近90天 ：WHERE date >= date_sub(current_date, 90)
-- 最近180天：WHERE date >= date_sub(current_date, 180)

-- 注意：Hive 的 / 恒返回 double，整除必须用 div（SQLite 的 / 对整数即整除，原公式在 SQLite 下成立）
```

**3. 关键解析**：

- **季度公式 `(m-1) div 3 + 1`**：这是一个整除分桶公式。1-3 月 → `(0,1,2) div 3 + 1` = `Q1`；4-6 月 → `(3,4,5) div 3 + 1` = `Q2`；以此类推。先减 1 是为了让 1-3 月从 0 开始整除，保证每 3 个月落进同一个桶。`cast(... as string)` 是 Hive 口径（SQLite 用 `CAST(... AS TEXT)`）。**Hive 中整除必须用 `div`，`/` 恒返回 double**（如 3 月：`(3-1)/3+1 = 1.666...`，结果错误）。
- **半年度公式 `(m-1) div 6 + 1`**：同理，每 6 个月一个桶。1-6 月 → `H1`，7-12 月 → `H2`。同样必须用 `div`。
- **year 写法**：`substr(date, 1, 4)` 即可，详见 1.4 速查表。

**4. 知识点延伸**：

- **季度公式的推导（吸收 11_02）**：关键在于 `(month-1) div 3` 这一步——它是整除分桶的标准写法。将连续值映射到离散桶号时，先减去起始偏移（`-1`），再除以桶宽（`div 3`），最后加起始桶号（`+1`）。这个模式可以推广到任意等宽分桶场景，如：将 1-100 分成 10 桶用 `(val-1) div 10 + 1`。
- **year 写法交叉引用 1.4 速查表**：年份提取 `substr(date, 1, 4)` 在 1.4 节已有覆盖，此处不再赘述。
- **Hive vs SQLite 口径差异**：Hive 中整数转字符串用 `cast(col as string)`，SQLite 用 `CAST(col AS TEXT)`。功能等价，只是方言关键字不同。

**5. 面试追问**：

- **Q: 为什么不用内置的 `quarter()` 函数？** A: 各引擎对日期函数的支持差异很大——MySQL/PostgreSQL 有 `QUARTER()`，Hive 有 `QUARTER()`（需要 date 类型），SQLite 完全没有。手写公式 `(m-1)/3 + 1` 是纯算术，不依赖任何引擎特性，最保险。而且面试中考的就是你能否现场推导这个公式。
- **Q: 滚动 12 个月的边界怎么定？** A: 用日期差（`date_sub(current_date, 365)`）而非月份差。用 365 天而非 12 个月是因为后者在不同引擎中语义不同（有的含当月，有的不含）。口径要和业务方确认：是否包含端点、是否用自然月还是滚动天。另外闰年时 365 天会有微小偏差，大数据场景通常可忽略。

</details>

---

### Q18. JSON 解析系列 `★★★☆☆` `json` `解析`

> 来源：项目题号 `13_01`　表：`json_table`

| id | data                                           |
|----|------------------------------------------------|
| 1  | {"name":"tom","age":18,"items":["a","b"]}      |
| 2  | {"name":"jerry","age":20,"items":["c"]}        |

解析 JSON 字段，提取嵌套键值并展开数组。

*提示：get_json_object 提取字段，lateral view explode 展开数组*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：Hive 解析 JSON 分两步——用 `get_json_object` 按 JSONPath 提取标量字段，用 `get_json_object` 取数组字符串后再 `SPLIT` + `EXPLODE` 展开为数组元素行。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 提取标量字段
SELECT id,
       get_json_object(data, '$.name') AS name,
       get_json_object(data, '$.age')  AS age
FROM json_table;

-- 展开 JSON 数组
-- get_json_object 返回字符串如 '["a","b"]'，
-- 需 regexp_replace 去掉引号和方括号，再 split + explode
SELECT id,
       get_json_object(data, '$.name') AS name,
       trim(regexp_replace(raw_item, '["\\[\\]]', '')) AS item
FROM json_table
LATERAL VIEW EXPLODE(
    SPLIT(
        regexp_replace(
            get_json_object(data, '$.items'),
            '[\\[\\]"\\s]', ','
        ),
        ','
    )
) t AS raw_item
WHERE trim(raw_item) != '';
```

**3. 关键解析**：

- **`get_json_object(data, '$.name')`**：按 JSONPath 语法提取 JSON 字符串中的标量值。`$.name` 取顶层 key，`$.a.b[0].c` 取嵌套路径。
- **数组展开的两步处理**：`get_json_object(data, '$.items')` 返回的是 JSON 字符串 `'["a","b"]'`，不是 Hive 数组。需要先用 `regexp_replace` 去掉方括号和引号，再用 `SPLIT` 按 `,` 拆分，最后 `EXPLODE` 展开为多行。
- **`regexp_replace` 的正则**：`[\\[\\]"\\s]` 匹配方括号、双引号和空白，统一替换为逗号（分隔符），便于后续 `SPLIT`。
- **局限性**：此 regexp_replace + split 方案仅适合无逗号的简单字符串数组。若数组元素本身含逗号（如 `'["hello,world","foo"]'`），split 会在错误位置截断。生产环境建议用 `json_tuple` 或复杂类型（`ARRAY<STRING>`）落地，避免正则解析 JSON 的脆弱性。

**4. 知识点延伸**：

- **`json_tuple` 一次取多字段**：`LATERAL VIEW json_tuple(data, 'name', 'age', 'city') t AS name, age, city` 比多次调用 `get_json_object` 更高效——只解析一次 JSON，而不是每个字段解析一趟。适合平铺提取多个字段。
- **嵌套路径 `$.a.b[0].c`**：`get_json_object` 支持完整的 JSONPath 语法，可以取任意深度的嵌套值和数组元素。如 `$.items[0]` 取数组第一个元素。
- **JSON 存表 vs 拆列**：数仓规范中，JSON 通常在 ETL 阶段就落地为独立列（结构化拆列）或复杂类型（`ARRAY<STRING>`、`MAP<STRING,INT>`、`STRUCT`）。查询时直接操作列比每次解析 JSON 高效得多。JSON 进数仓通常只作为临时/脏数据的过渡形态。

**5. 面试追问**：

- **Q: `get_json_object` 和 `json_tuple` 选哪个？** A: 单字段提取或需要取嵌套路径（如 `$.a.b[0]`）时用 `get_json_object`；一次提取多个平铺字段时用 `json_tuple`，只解析一次 JSON 性能更好。两者可以混用。
- **Q: JSON 数据存表里好还是拆成独立列好？** A: 数仓规范一般落地为独立列或复杂类型（`ARRAY`/`MAP`/`STRUCT`），避免每次查询都做 JSON 解析。JSON 存表适合：schema 不稳定的临时数据、需要保留原始结构的数据。落地到正式表时应在 ETL 阶段拆列。

> 📌 SQLite 等价写法：
> ```sql
> -- 提取标量字段
> SELECT id,
>        json_extract(data, '$.name') AS name,
>        json_extract(data, '$.age')  AS age
> FROM json_table;
>
> -- 展开 JSON 数组
> SELECT id,
>        json_each.value AS item
> FROM json_table, JSON_EACH(json_table.data, '$.items');
> ```

</details>

---

## 组9 综合与建模

### Q19. 接雨水问题 `★★★★★` `趣味` `算法` `接雨水`

> 来源：项目题号 `14_01`　表：`heights`

| height |
|--------|
| 0      |
| 1      |
| 0      |
| 2      |
| 1      |
| 0      |
| 1      |
| 3      |
| 2      |
| 1      |
| 2      |
| 1      |

给定柱子高度数组，计算能接多少雨水。

*提示：每个位置的储水量 = min(左边最高, 右边最高) - 当前高度；用 max() over(order by) 分别计算左右两边的滚动最大值*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：把数组转成行表后，对每行分别计算左侧滚动最大值和右侧滚动最大值，利用木桶效应：储水量 = 两侧最高柱的较小者 - 当前行高度。

**2. 参考 SQL（Hive 方言）**：

```sql
-- step 1: 给行编号，把"数组题"变成"行题"
WITH numbered AS (
    SELECT ROW_NUMBER() OVER () AS idx, height
    FROM heights
),
-- step 2: 左侧滚动最大值（从左往右）
left_max AS (
    SELECT idx, height,
           MAX(height) OVER (ORDER BY idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS lmax
    FROM numbered
),
-- step 3: 右侧滚动最大值（从右往左，反向帧）
right_max AS (
    SELECT idx, height, lmax,
           MAX(height) OVER (ORDER BY idx DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rmax
    FROM left_max
)
-- step 4: 求总储水量
SELECT SUM(LEAST(lmax, rmax) - height) AS total_water
FROM right_max
WHERE LEAST(lmax, rmax) > height;
```

**3. 关键解析**：

- **`ROW_NUMBER() OVER () AS idx`**：`heights` 表没有位置列，需要 `row_number()` 给每行编号，将"数组"转换为带索引的"行表"，后续窗口排序才有依据。
- **左侧滚动最大值 `MAX(height) OVER (ORDER BY idx ... PRECEDING AND CURRENT ROW)`**：从第 1 行到当前行的 height 最大值，即"左边比当前高的柱子中最高的"。
- **右侧滚动最大值 `ORDER BY idx DESC`**：降序排列后取 UNBOUNDED PRECEDING 到 CURRENT ROW，等价于原始顺序中"从当前行到最后一行的最大值"，即右边的最高柱。
- **`LEAST(lmax, rmax) - height`**：木桶效应——水位由两侧较矮的那根柱子决定，减去当前柱高就是该位置的储水量。

**4. 知识点延伸**：

- **算法题 SQL 化的一般套路**：先找"逐行可计算的局部量"（左侧最大值、右侧最大值），再用窗口函数/聚合将局部量组合成最终结果。大多数数组类算法题都可以用这个思路搬到 SQL 中。
- **反向帧技巧**：`ORDER BY idx DESC` + `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` 可以实现"从右往左"的滚动计算，是处理双向扫描类问题的标准手法。

**5. 面试追问**：

- **Q: 为什么两端柱子不接水？** A: `LEAST(lmax, rmax)` 中必有一侧是自身高度（最左端 rmax 包含自身、最右端 lmax 包含自身），差值一定为 0，被 `WHERE LEAST(lmax, rmax) > height` 过滤掉。
- **Q: Hive 里多参数取最小值用哪个函数？** A: `LEAST(a, b, ...)`。SQLite（及 MySQL 等部分引擎）多参取小用 `MIN(a, b, ...)`——这是方言差异的常见坑点。注意 `MIN()` 在多数 SQL 中是聚合函数，但 SQLite 允许它做标量多参取小，Hive/Spark 则严格区分 `LEAST()`（标量）和 `MIN()`（聚合）。

> 📌 SQLite 等价写法：
> ```sql
> -- SQLite 用 MIN() 替代 LEAST()，其余窗口语法相同
> WITH numbered AS (
>     SELECT ROW_NUMBER() OVER () AS idx, height
>     FROM heights
> ),
> left_max AS (
>     SELECT idx, height,
>            MAX(height) OVER (ORDER BY idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS lmax
>     FROM numbered
> ),
> right_max AS (
>     SELECT idx, height, lmax,
>            MAX(height) OVER (ORDER BY idx DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rmax
>     FROM left_max
> )
> SELECT SUM(MIN(lmax, rmax) - height) AS total_water
> FROM right_max
> WHERE MIN(lmax, rmax) > height;
> ```

</details>

---

### Q20. 赛马问题 `★★★★☆` `趣味` `赛马` `非等值关联`

> 来源：项目题号 `14_03`　表：`race_result`

| horse | time |
|-------|------|
| 甲    | 9.8  |
| 乙    | 10.2 |
| 丙    | 9.9  |

如何用 SQL 解决趣味赛马问题（非等值关联匹配）——为每匹马找到比它快的那匹马。

*提示：非等值 JOIN 模拟排序，子查询取前一个值*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：通过非等值关联 `b.time < a.time` 找出每匹马所有比它快的马，再用相关子查询 `MIN(time)` 收敛到"紧邻更快的那匹"。

**2. 参考 SQL（Hive 方言）**：

```sql
-- 非等值关联：找每匹马比自己快的前一匹
SELECT a.horse, a.time,
       b.horse AS faster_horse
FROM race_result a
LEFT JOIN race_result b ON b.time < a.time
WHERE b.time = (SELECT MIN(time) FROM race_result WHERE time < a.time);
```

**3. 关键解析**：

- **`b.time < a.time`**：非等值关联条件，匹配所有 time 比当前马小的记录——即所有更快的马。
- **`WHERE b.time = (SELECT MIN(time) FROM race_result WHERE time < a.time)`**：在所有更快马中，取 time 最小的（即最接近的、紧邻的更快者），从笛卡尔结果中筛选出唯一一行。
- **`LEFT JOIN` + WHERE 退化为 INNER JOIN**：虽然使用了 LEFT JOIN，但 `WHERE b.time = (子查询返回 NULL)` 中 `NULL = NULL` 恒为 UNKNOWN（非 TRUE），最快的马（无更快者，子查询返回 NULL）实际被 WHERE 过滤掉——LEFT JOIN 在此退化为 INNER JOIN 效果。若要保留最快的马，需将条件挪进 ON 子句（`ON b.time < a.time AND b.time = (SELECT MIN(...))`），或更优雅地使用下方 LAG 解法。这个"LEFT JOIN + WHERE 退化"本身是高频面试考点。

**4. 知识点延伸**：

- **更优雅的窗口解法（面试加分）**：用 `LAG` 一步到位，避免非等值 JOIN 的笛卡尔放大：

```sql
SELECT horse, time,
       LAG(horse) OVER (ORDER BY time) AS faster_neighbor
FROM race_result;
```

按 time 排序后，`LAG` 直接取前一行（即紧邻更快的那匹马），无需 JOIN 和子查询。这是更推荐的生产写法。

- **非等值 JOIN 的风险**：`b.time < a.time` 会产生笛卡尔乘积放大（每行匹配行数不固定），无法使用 hash join，只能走 nested loop，大数据量下性能极差。生产环境应优先使用窗口函数替代。

**5. 面试追问**：

- **Q: 非等值 JOIN 有什么问题？** A: 无法按 join key 做 hash 分桶，只能走 nested loop（嵌套循环），时间复杂度 O(n^2)。而且会产生数据放大（每行匹配行数不固定），结果集可能远大于原表。生产环境大数据量下基本禁用。
- **Q: 一条 SQL 顺手解决的话怎么写？** A: `LAG(horse) OVER (ORDER BY time)` 一步到位——按 time 升序排列后，LAG 取前一行即紧邻更快者。比非等值 JOIN + 子查询更简洁高效。
- **Q: 这里的 LEFT JOIN 真的保留了最快的马吗？** A: 并没有。WHERE 中 `NULL = NULL` 恒为 UNKNOWN（非 TRUE），最快的马（子查询返回 NULL）被 WHERE 过滤——LEFT JOIN 退化为 INNER JOIN。这是经典的面试陷阱：LEFT JOIN 保左表全量仅当 WHERE 不含右表列的 NULL 过滤条件时才成立。

</details>

---

### Q21. 人事数仓表格设计 `★★★☆☆` `数仓` `表格设计` `人事`

> 来源：项目题号 `10_02`　表：`employee`, `salary`, `attendance`

本题无表结构，为建模设计题。

设计人事数仓核心表结构：员工表、薪资表、考勤表。

*提示：标准数仓建模——事实表 + 维度表，星型/雪花模型*

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：按数仓建模最佳实践，将表分为维度表（描述"谁"，变化慢）和事实表（记录"发生了什么"，按周期增长），围绕核心业务（员工薪资、考勤）设计星型或雪花模型。

**2. 参考建表语句（带建模注释）**：

```sql
-- ========================================
-- 维度表：描述"谁"
-- ========================================

-- 员工维度表（变化慢，记录员工基本信息）
-- 是整个数仓的核心维度，薪资和考勤事实表都通过 emp_id 关联
CREATE TABLE employee (
    emp_id    INTEGER PRIMARY KEY,  -- 员工唯一标识，全表主键
    name      TEXT,                 -- 员工姓名
    dept_id   INTEGER,             -- 部门 ID（可外键关联部门表，形成雪花模型）
    hire_date TEXT,                -- 入职日期
    status    TEXT                  -- 在职状态（active/inactive/resigned）
);

-- ========================================
-- 事实表：记录"发生了什么"
-- ========================================

-- 薪资事实表（按月增长，每月每员工一条）
-- 联合主键 (emp_id, month) 支撑周期快照事实表设计
CREATE TABLE salary (
    emp_id      INTEGER,            -- 员工 ID（维度代理键，冗余以避免频繁 JOIN）
    month       TEXT,               -- 薪资月份（如 '2024-01'）
    base_salary REAL,               -- 基本工资
    bonus       REAL,               -- 奖金
    PRIMARY KEY (emp_id, month)    -- 联合主键：同一员工同月只有一条记录
);

-- 考勤事实表（按天增长，每日每员工一条）
CREATE TABLE attendance (
    emp_id    INTEGER,             -- 员工 ID
    date      TEXT,                 -- 考勤日期
    check_in  TEXT,                 -- 签到时间
    check_out TEXT                  -- 签退时间
);
```

**3. 关键解析**：

- **维度表 vs 事实表**：`employee` 是维度表（描述主体"谁"，数据量小、变化慢）；`salary` 和 `attendance` 是事实表（记录事件"发生了什么"，按时间周期持续增长）。数仓设计的核心就是区分这两类表并建立关联。
- **星型 vs 雪花模型**：当前设计为星型模型——事实表（salary/attendance）居中，直接通过 emp_id 关联维度表（employee），查询时只需一次 JOIN。如果部门信息拆为独立的 department 表，employee 再关联 department，就形成雪花模型（维度再规范化），查询需要多一次 JOIN。
- **联合主键 `(emp_id, month)`**：保证同一员工同月只有一条薪资记录，这是周期快照事实表（periodic snapshot fact table）的标准设计。

**4. 知识点延伸**：

- **拉链表处理员工维度缓慢变化（SCD）**：当员工调部门或改状态时，维度表需要保留历史。拉链表通过 `start_date` / `end_date` 两个时间字段实现：新增一条记录写入新值和 start_date，旧记录的 end_date 设为新记录生效日期的前一天。查询时加 `WHERE start_date <= 当前日期 AND end_date > 当前日期` 即取到当前有效记录。
- **emp_id 冗余在事实表的原因**：本题中 `emp_id` 是业务自然键，数仓标准做法是事实表放维度的代理键（另行生成的 surrogate key）。本题为简化直接用 emp_id 关联，实际生产中事实表冗余代理键而非自然键，查询时通过代理键 JOIN 维度表获取详细信息，既控制事实表宽度，又保证查询性能。

**5. 面试追问**：

- **Q: 星型模型和雪花模型怎么选？** A: 数仓默认选星型模型——事实表直接关联维度表，查询 JOIN 少、性能好，适合 OLAP 场景。雪花模型对维度进一步规范化（拆子维度表），减少数据冗余但增加 JOIN 次数。选型权衡：查询性能（少 JOIN）vs 存储冗余控制，大多数数仓场景下星型模型是更实用的选择。
- **Q: 员工调部门的历史怎么保留？** A: 用拉链表（start_date / end_date）。每次部门变动插入一条新记录，旧记录关闭 end_date。查询时用 `WHERE start_date <= ? AND end_date > ?` 取当前有效行。这与 Q3 的区间分段思想一脉相承——用起止时间区间来表示一个状态的生效周期。

</details>
