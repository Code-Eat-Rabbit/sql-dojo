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

<!-- APPEND -->
