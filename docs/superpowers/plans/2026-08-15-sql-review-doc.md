# SQL 面试复习手册 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 生成 `docs/sql-interview-review.md`——单文件 SQL 面试复习手册（Part 1 知识速查 + Part 2 精选 21 题，答案折叠可自测，Hive 方言口径）。

**架构：** 纯新增 Markdown 文档，不改动任何代码。数据来源为 `data_builder/manifest.py`（题面/答案/提示）与各 `.db` 表结构。分 10 个任务增量写入并频繁 commit。

**技术栈：** Markdown（GitHub 风格，`<details>` 折叠块）。无代码依赖。

**规格：** `docs/superpowers/specs/2026-08-15-sql-review-doc-design.md`

---

## 全局约定（每个任务都必须遵守）

1. **只写一个文件**：`docs/sql-interview-review.md`。本计划中的"追加"指在该文件末尾续写（任务 1 创建）。
2. **commit 纪律**：工作区存在与本任务无关的未提交改动（`backend/routers/databases.py`、`backend/routers/problems.py`）。每次 commit **只能** `git add docs/sql-interview-review.md`，严禁 `git add -A` / `git add .`。
3. **题目数据来源**：所有题面、参考 SQL、提示均取自 `data_builder/manifest.py`（下方每题卡片已注明行号，执行时 Read 对应行号段核对原文，禁止凭记忆改写题面）。
4. **每题模板**（Part 2 全部 21 题统一）：

```markdown
### Q<n>. <题目标题> `难度<★重复difficulty次>` `<tags中的来源标签>`

> 来源：项目题号 `<id>`　表：`<tables>`

<表结构：每题卡片给出的列定义，3-5 行，附 2-3 行示例数据>

<题目描述：改写自 manifest description，只保留中文，去掉 English 行>

提示（来自 manifest hints，弱化为斜体一行）

<details><summary>💡 思路与答案（点开前先自己想 5 分钟）</summary>

**1. 解题思路**：先一句话说套路，再 2-4 行讲步骤

**2. 参考 SQL（Hive 方言）**：分步注释代码块

**3. 关键解析**：只在"为什么这么写"的行上解释，不逐行复读

**4. 知识点延伸**：按每题卡片列出的条目写（变式/多解法/相关函数）

**5. 面试追问**：按每题卡片列出的 Q&A 写

（如涉及方言差异，末尾加一行：> 📌 SQLite 等价写法：...）

</details>
```

5. **难度星标**：`difficulty` 1-5 → `★☆☆☆☆`、`★★☆☆☆`、`★★★☆☆`、`★★★★☆`、`★★★★★`。
6. **Q 编号固定分配**（全文包括速查表交叉引用都必须用这套编号）：

| Q | id | Q | id | Q | id |
|---|---|---|---|---|---|
| Q1 | 01_01 | Q8 | 04_02 | Q15 | 08_01 |
| Q2 | 01_03 | Q9 | 04_06 | Q16 | 08_02 |
| Q3 | 01_07 | Q10 | 05_01 | Q17 | 11_03 |
| Q4 | 02_01 | Q11 | 09_02 | Q18 | 13_01 |
| Q5 | 02_03 | Q12 | 06_01 | Q19 | 14_01 |
| Q6 | 03_01 | Q13 | 06_02 | Q20 | 14_03 |
| Q7 | 04_01 | Q14 | 07_01 | Q21 | 10_02 |

7. **覆盖映射**（16 道未选题的吸收归处，任务 10 会逐条验收；归处必须是该位置实际出现的实质内容，不是提一嘴题号）：

| 未选题 | 归处 | 未选题 | 归处 |
|---|---|---|---|
| 01_02 | Q1 延伸-变式 | 04_07 | Q9 延伸-变式 |
| 01_04 | 1.2 速查"连续问题"行 | 04_08 | Q7 延伸（含原答案勘误） |
| 01_05 | Q1 延伸-变式 | 06_03 | Q13 面试追问 |
| 01_06 | Q3 延伸 | 09_01 | Q11 延伸 |
| 02_02 | Q4 延伸-基础用法 | 10_01 | 1.5 追问清单末条 |
| 03_02 | Q6 延伸-变式 | 11_01 | 1.4 速查表 year 行 |
| 04_03 | Q8 延伸-变式 | 11_02 | Q17 延伸 |
| 04_04 | Q8 延伸-变式 | — | — |
| 04_05 | Q8 延伸-变式 | — | — |

---

### 任务 1：文档骨架 + 使用说明 + Part 1 的 1.1/1.2

**文件：**
- 创建：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入骨架与 Part 1 前两节**

写入以下完整内容（`<!-- APPEND -->` 标记是文档结尾占位，后续任务在其前追加；任务 10 删除）：

````markdown
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

<!-- APPEND -->
````

- [ ] **步骤 2：结构验收**

运行：`grep -c '^## 1\.' docs/sql-interview-review.md`
预期：`2`（即 1.1、1.2 两节）。
运行：`grep -c '<details>' docs/sql-interview-review.md`
预期：`0`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add handbook skeleton with window-function and pattern cheatsheets"
```

---

### 任务 2：Part 1 的 1.3/1.4/1.5

**文件：**
- 修改：`docs/sql-interview-review.md`（在 `<!-- APPEND -->` 前插入）

- [ ] **步骤 1：写入三节**

````markdown
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
````

- [ ] **步骤 2：结构验收**

运行：`grep -c '^## 1\.' docs/sql-interview-review.md`
预期：`5`。
运行：`grep -c '<details>' docs/sql-interview-review.md`
预期：`0`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add join/date-function/interview-question cheatsheets"
```

---

### 任务 3：Part 2 组 1 连续问题（Q1-Q3）

**文件：**
- 修改：`docs/sql-interview-review.md`（`<!-- APPEND -->` 前追加）

- [ ] **步骤 1：写入组标题与三题**

组标题：`# Part 2 精选题册` + `## 组1 连续问题`，然后按全局模板写三题。每题要点卡：

**Q1（01_01，manifest.py:71-107，难度2，标签`字节面试题`）**
- 表：`test(id INTEGER, date TEXT)`，示例 `(1, '2024-01-01 08:00:00')`、`(1, '2024-01-01 20:00:00')`、`(1, '2024-01-02 09:00:00')`
- 原答案（manifest 84-100 行）可直接采用，但要把步骤一二三组装为一条可执行完整 SQL（用两层子查询嵌套替换"（步骤一）"占位），保留分步注释。整理时把 `substr(date,1,10)` 保留并注明：datetime 截日期，Hive 可用 `to_date(date)`。
- 思路要点：同一日期去重后，连续日期与 row_number 同为等差数列，相减差值恒定 → 差值即分组键。
- 延伸（吸收 01_02、01_05）：
  - 变式 1（01_02 求最大连续天数）：在第三步结果上再 `select id, max(day_cnt) ... group by id`，给出完整 SQL。
  - 变式 2（01_05 余额>1000 连续天数，外汇公司）：`where balance > 1000` 先过滤再套差值法，用 CTE 写完整 SQL；强调"先过滤后连续"顺序不能反。
  - 相关函数：`date_sub` 与 `date_add` 等价（负天数）；`group by` 去重的原理。
- 面试追问：
  - Q: 为什么必须先去重？A: 一天多次登录会让 row_number 错位，差值法失效。
  - Q: "连续 3 天以上"含不含恰好 3 天？A: 口径要当场确认，`having count(*) >= 3` 与 `> 3` 一字之差。
  - Q: 为什么减 row_number 后差值会相同？A: 日期与序号同步 +1 递增，作差后常数项抵消——本质是等差数列性质。

**Q2（01_03，manifest.py:135-178，难度3）**
- 表同 Q1。
- 原答案（151-172 行）三种方法照录并组装完整；方法 1 指向 Q1 不重复贴。
- 关键解析：方法 2 用 `lag(date,1)`/`lag(date,2)` 取前两天，`datediff` 全为 1 判定连续；方法 3 三次自关联逐级 `datediff=1`。
- 延伸：三种方法对比表——row_number 法通用（任意 N 天）、lag 法要 N-1 个前值（N 大时不可扩展）、自关联法 O(n²) 性能最差但不用窗口函数（面试展示 SQL 基本功）。
- 面试追问：
  - Q: N 很大（连续 30 天）用哪个？A: row_number 差值法，lag 要写 29 个前值。
  - Q: 自关联法的性能风险？A: 每次自关联近似 n² 次比较，大数据量必炸。
  - Q: datediff 方向？A: `datediff(a,b)` = a-b（天数），别记反。

**Q3（01_07 连胜数，manifest.py:273-319，难度3）**
- 表：`games(user_id, date, result)`，result ∈ {'win','lose'}，示例 `(1,'2024-01-01','win'),(1,'2024-01-02','win'),(1,'2024-01-03','lose')`
- 原答案两个解法照录（284-312 行）。解析重点：解法 1 双 row_number——先 `where result='win'` 过滤，`rn`（全行序）与 `rn2`（win 行序）的差在"连续 win 段"内恒定；解法 2 lag+case 造断点标记、`sum() over` 累加分段。
- 延伸（吸收 01_06 集度面试题）：日期区间合并——`lag(end_date)` 与当前 `start` 差 1 天以上造 0/1 断点标记，`sum(flag) over` 累加为组号，组内 `min(start_date), max(end_date)`。给出 01_06 的完整 Hive SQL（把原答案 manifest 244-263 行中 `DATE_ADD(x, INTERVAL 1 DAY)` 改为 `date_add(x, 1)`，表名 `mydb.test_xiaoming` 改为 `test_xiaoming`，`NAME` 改 `name`）。指出该模式与解法 2 同构：**"断点标记 + 累加分段"**。
- 面试追问：
  - Q: 连续的"单位"从日期换成状态/数值怎么办？A: 套路不变，先过滤/标记成 0/1，再分段。
  - Q: 双 row_number 差值为什么能分组？A: win 行之间若被 lose 隔断，rn 与 rn2 的增速不同步，差值跳变。

- [ ] **步骤 2：结构验收**

运行：`grep -c '^### Q' docs/sql-interview-review.md` → 预期 `3`；`grep -c '<details>' docs/sql-interview-review.md` → `3`；`grep -c '</details>' docs/sql-interview-review.md` → `3`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add group-1 consecutive-pattern problems Q1-Q3"
```

---

### 任务 4：组 2 开窗 lead/lag（Q4-Q5）+ 组 3 排序（Q6）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入三题**

**Q4（02_01 波峰波谷，manifest.py:329-357，难度3）**
- 表：`stock_price(id, ds, price)`，示例 `(1,'2024-01-01',10.0),(1,'2024-01-02',12.5),(1,'2024-01-03',11.0)`
- 原答案照录（341-350 行）。解析：lag 前值、lead 后值必须包一层子查询再 `case when`（部分引擎允许直接嵌套，包一层最稳）。
- 延伸（吸收 02_02）：lag/lead 基础——`lag(col, n, default)` 三参数：列、偏移量、越界默认值；首行 lag 为 NULL 的处理 `lag(price, 1, price)` 用自身填充。
- 面试追问：Q: 首尾行为 NULL 怎么办？A: 第三参 default 或 `coalesce`。Q: 相等算峰吗？A: 严格大于/小于，边界口径确认。

**Q5（02_03 变化率，manifest.py:382-403，难度3，标签`面试`）**
- 表：`metrics(date, value)`，示例 `('2024-01-01',100),('2024-01-02',120)`
- 原答案照录（393-397 行）。解析：环比 = (今-前)/前，`round(...,2)` 保留两位；`*100.0` 防整数除法。
- 延伸：同比 vs 环比口径；首行 NULL 变化率显示问题。
- 面试追问：Q: 前值为 0 怎么办？A: `case when prev = 0 then null else ...`，除零必须防。

**Q6（03_01 三种排序，manifest.py:413-442，难度2）**
- 表：`scores(student, score)`，示例数据必须有并列：`('a',90),('b',90),('c',85)`——演示三函数差异的关键。
- 原答案照录（429-434 行），配一张三函数输出对照表（用示例数据逐行列出 rn/rk/dr 的值）。
- 延伸（吸收 03_02 每个学生第二高科目）：`dense_rank() over(partition by student order by score desc)` 取 `dr=2`，给出完整 SQL；说明为何不用 rank（并列第一跳号后可能没有第 2 名）。
- 面试追问：Q: TopN 并列只取一条？A: row_number。Q: 取第 N 高为什么 dense_rank？A: 并列不跳号，N 一定存在。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `6`；`grep -c '<details>'` → `6`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add lead/lag and ranking problems Q4-Q6"
```

---

### 任务 5：组 4 累计汇总（Q7-Q9）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入三题**

**Q7（04_01 累计访问，manifest.py:479-499，难度2）**
- 表：`user_visits(user_id, month_id, visit_cnt_1m)`，示例 `(1,'202401',30),(1,'202402',25)`
- 原答案照录（490-492 行）。解析：`sum over` 加 `order by` 变累计、去掉 `order by` 变组内总量——同一条 SQL 两种语义，逐行对照演示。
- 延伸（吸收 04_08 历史新低，含勘误）：`min(price) over(partition by id order by ds)` 滚动最小值求历史新低。**必须写勘误框**：manifest 原答案（681-691 行）把 `LAG(price) OVER(...)` 直接写在 `WHERE` 里——窗口函数不能出现在 WHERE（WHERE 先于窗口计算执行），正确写法是在 CTE 中先算好 `min_so_far` 与 `prev_price` 再过滤：

```sql
WITH marked AS (
    SELECT id, ds, price,
           MIN(price) OVER (PARTITION BY id ORDER BY ds) AS min_so_far,
           LAG(price)  OVER (PARTITION BY id ORDER BY ds) AS prev_price
    FROM product_price
)
SELECT id, ds, price
FROM marked
WHERE price = min_so_far
  AND prev_price IS NOT NULL   -- 排除首日（无历史可比）
  AND price < prev_price;      -- 严格新低
```

- 面试追问：Q: rows 与 range 帧的区别？A: 物理行 vs 排序值（同值同帧）。Q: 窗口函数能写进 where 吗？A: 不能，SQL 执行顺序 WHERE 先于 SELECT 中的窗口计算，需包一层/CTE。

**Q8（04_02 同时在线峰值，manifest.py:501-535，难度3）**
- 表：`live_log(room_id, user_id, login_time, logout_time)`，时间格式 `yyyymmdd HH:MM:SS`，示例 `(101,1,'20210310 08:00:00','20210310 09:30:00')`
- 原答案组装完整可执行 SQL（513-528 行的三步合成一条，子查询替换"（步骤一）"占位）。解析：进出事件 +1/-1 是把"区间问题"转成"事件流问题"的关键抽象。
- 延伸（吸收 04_03/04_04/04_05 三个变式，各给完整 SQL）：
  - 每小时峰值（04_03）：最外层加 `substr(event_time,1,10)` 拼小时粒度分组。
  - 不限时段（04_04）：去掉步骤一的两个日期 WHERE。
  - 峰值时间（04_05）：累计后 `rank() over(partition by room_id order by online_cnt desc)` 取 rk=1；**必须讲原答案细节**：`order by event_time, user_type` 让 -1 排在 +1 前——同一时刻"先出后进"的保守口径（04_05 在 597-616 行）。
- 面试追问：Q: 用 union 还是 union all？A: union all，进出场事件可能同值但语义不同，去重会丢事件。Q: 同一秒有人进有人出算几个在线？A: 口径题——保守取 -1 先处理（峰值不虚高）。

**Q9（04_06 美团-累计消费首次达标日期，manifest.py:624-649，难度5，标签`美团`）**
- 表：`user_spend(user_id, dt, price)`，示例 `(1,'2024-01-01',300),(1,'2024-01-02',500),(1,'2024-01-03',400)`
- 原答案照录（635-643 行）。解析：累计 → 达标行筛选 → `min(dt)` 取最早；"首次达到"= 对达标日期取最小。
- 延伸（吸收 04_07 复购）：`group by user_id, product_id having count(distinct order_id) >= 2`，给完整 SQL；讲 count(distinct) vs count(*) 口径（一单多行时）。
- 面试追问：Q: 为什么 min(dt) 还要 group by user_id？A: 达标后可能持续达标，取最早一条。Q: having 和 where 的执行时机？A: where 过滤行（聚合前），having 过滤组（聚合后）。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `9`；`grep -c '<details>'` → `9`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add cumulative-aggregation problems Q7-Q9"
```

---

### 任务 6：组 5 区间与 NULL（Q10-Q11）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入两题**

**Q10（05_01 区间合并，manifest.py:706-737，难度4）**
- 表：`raw_intervals(start, end)`，示例 `(1,3),(2,5),(8,10)`
- 原答案照录（717-730 行）。解析三点：① 为什么用 `max(end) over(前置行)` 而不是 `lag(end)`——前面的区间可能很长，只看上一行会漏；② 帧 `ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING` 排除当前行；③ `sum(new_group) over` 累加成组号后按组取 min/max。
- 延伸：与 Q3 延伸（01_06 lag 断点法）对比——数据无重叠时 lag 够用，有重叠/嵌套必须滚动 max。
- 面试追问：Q: 区间是日期不是数字怎么办？A: datediff 转数值或直接比较日期大小，套路不变。Q: 首行的 max_end_so_far 是 NULL，case 怎么走？A: `start > NULL` 为 NULL→else 分支 0，首行天然归第一组，行为正确（讲清楚这个隐式依赖）。

**Q11（09_02 缺失值填充 forward fill，manifest.py:954-979，难度3）**
- 表：`data_table(id, date, value)`，value 含 NULL，示例 `(1,'2024-01-01',10),(1,'2024-01-02',NULL),(1,'2024-01-03',NULL),(1,'2024-01-04',20)`
- 原答案照录（966-975 行）。解析：相关子查询 = 每行触发一次"找最近非空前值"（`order by date desc limit 1`）；性能警告 O(n²)。
- 延伸（吸收 09_01 状态标记）：`lead(start_time) over(partition by id order by start_time) as end_time` 给状态区间补终点，给完整 SQL；Hive 备注写法：子查询内 LIMIT 在部分 Hive 版本不支持，可改 `row_number` 取最近一行。
- 面试追问：Q: forward fill 的窗口函数解？A: `last_value(value ignore nulls)`（部分引擎支持 IGNORE NULLS；Hive 的 last_value 不忽略 NULL，需 case+max 技巧或递归 CTE，答出权衡即可）。Q: 相关子查询为什么慢？A: 每行执行一次子查询，无法批量。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `11`；`grep -c '<details>'` → `11`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add interval-merge and forward-fill problems Q10-Q11"
```

---

### 任务 7：组 6 JOIN（Q12-Q13）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入两题**

**Q12（06_01 每科>60 的学生全部成绩，manifest.py:747-771，难度3）**
- 表：`student(id, student_name)`、`class(id, class_name)`、`sc(sid, cid, score)`，示例 `(1,'小明')`、`(10,'数学')`、`(1,10,88)`
- 原答案照录（758-764 行）。解析："所有科目都 >60"是全称量词，SQL 用双重否定实现：排除"存在一门 ≤60"的学生。
- 延伸：聚合解法 `group by sid having min(score) > 60`（给完整 SQL，再 join 回明细）；NOT IN 的 NULL 陷阱（子查询含 NULL 整体返回空 → NOT EXISTS 替代，给等价 SQL）。
- 面试追问：Q: not in 子查询里有 null 会怎样？A: 返回空集——not in 遇 NULL 恒 UNKNOWN。Q: "存在一门>60"和"所有科目>60"的 SQL 差异？A: 前者 where sid in (…score>60)，后者双重否定/having min。

**Q13（06_02 相互关注，manifest.py:773-804，难度3）**
- 表：`fans(from_user, to_user)`，示例 `('a','b'),('b','a'),('a','c')`
- 原答案两法照录（785-797 行）。解析：方法 1 自关联判互相 + `a.from_user < a.to_user` 去重（(a,b)/(b,a) 只留一条）；方法 2 双向 union all 后 count>=2。
- 延伸（吸收 06_03 千亿级优化，作为重点追问展开）：数据量千亿时的方案——① map-side join（小表广播进内存，免 shuffle）② 分桶表：按用户 id 分桶，同键数据同节点，join 变本桶连接 ③ Bloom filter 预过滤不可能匹配的键 ④ 核心原则：避免全量 shuffle join。
- 面试追问：Q: 为什么 where 里加 `<` 比较？A: 无向对去重。Q: 相互关注和"共同好友"区别？A: 前者是二元关系判定，后者要找交集（同套路扩展）。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `13`；`grep -c '<details>'` → `13`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add join problems Q12-Q13"
```

---

### 任务 8：组 7 留存（Q14）+ 组 8 转换/日期/JSON（Q15-Q18）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入五题**

**Q14（07_01 七日留存，manifest.py:836-866，难度3）**
- 表：`user_active(user_id, date)`，示例 `(1,'2024-01-01'),(1,'2024-01-08'),(2,'2024-01-01')`
- 原答案方言修正后写入：`DATE_ADD(a.first_date, INTERVAL 7 DAY)` → `date_add(a.first_date, 7)`（其余照录 847-858 行）。解析：首活 `min(date)` 定分母，`left join` 第 7 天活跃保分母不丢，`count(distinct)` 防重复活跃灌水。
- 延伸：留存家族口径表——次日/3日/7日/30日留存只需改偏移天数；新增用户口径 vs 活跃用户口径的区别（min(date) 限定首次出现）。
- 面试追问：Q: 为什么 left join 而不是 inner join？A: 分母必须完整，inner 会把未留存用户挤掉。Q: 用户第 7 天活跃多次算几次？A: count(distinct) 保证算一人。

**Q15（08_01 行转列，manifest.py:876-905，难度2）**
- 表：`user_tags(user_id, tags)`，示例 `(1,'a,b,c')`
- **主答案改写为 Hive（这是本题核心）**：

```sql
SELECT user_id, tag
FROM user_tags
LATERAL VIEW EXPLODE(SPLIT(tags, ',')) t AS tag;
```

- SQLite 等价写法备注：照录原递归 CTE（888-898 行），注明用于本项目本地练习。
- 延伸：`posexplode` 带序号展开；`lateral view outer`（空数组也保行）；split 后空字符串问题（`where tag != ''`）。
- 面试追问：Q: explode 和 lateral view 的关系？A: explode 是表生成函数，lateral view 是把它与原表行关联的语法。Q: tags 有空串元素？A: 过滤或 split 前清洗。

**Q16（08_02 列转行，manifest.py:907-925，难度2）**
- 表：`user_tag_rows(user_id, tag)`，示例 `(1,'a'),(1,'b'),(1,'c')`
- **主答案改写为 Hive**：`SELECT user_id, CONCAT_WS(',', COLLECT_LIST(tag)) AS tags FROM user_tag_rows GROUP BY user_id;`
- SQLite 等价写法备注：`group_concat(tag, ',')`（原答案 918-921 行）。
- 延伸：`collect_list` vs `collect_set`（保序重复 vs 去重）；聚合内排序 `sort_array(collect_list(tag))`。
- 面试追问：Q: 要去重且保序？A: collect_set + sort_array。Q: concat_ws 遇 NULL？A: 跳过（concat 则整体 NULL）。

**Q17（11_03 日期格式汇总，manifest.py:1093-1114，难度2）**
- 表：`date_table(date)`，date 格式 `yyyy-MM-dd`，示例 `('2024-03-15')`
- 原答案是注释清单（1104-1110 行），整理为**完整可执行对照表 SQL**：

```sql
SELECT date,
       substr(date, 1, 4)                                        AS yr,      -- 2024
       substr(date, 6, 2)                                        AS mm,      -- 03
       concat(substr(date,1,4), 'Q',
              cast((cast(substr(date,6,2) as int)-1)/3 + 1 as string)) AS qtr,  -- 2024Q1
       concat(substr(date,1,4), 'H',
              cast((cast(substr(date,6,2) as int)-1)/6 + 1 as string)) AS half, -- 2024H1
       substr(date, 1, 7)                                        AS ytm      -- 2024-03
FROM date_table;
-- last 系列（滚动窗口）：
-- last12m: WHERE date >= date_sub(current_date, 365)
-- last30d : WHERE date >= date_sub(current_date, 30)
```

- 延伸（吸收 11_02）：季度公式 `(m-1)/3+1` 的推导（整除分桶）；11_01 的 year 写法已在 1.4 速查表（交叉引用即可）。注明：`cast(... as string)` 是 Hive 口径（SQLite 用 `as text`）。
- 面试追问：Q: 为什么不用内置 quarter()？A: 各引擎支持不一，手写公式最保险，且要能现场推导。Q: 滚动 12 个月的边界？A: 用日期差不用月份差，口径要确认含不含端点。

**Q18（13_01 JSON 解析，manifest.py:1187-1214，难度3）**
- 表：`json_table(id, data)`，data 如 `'{"name":"tom","age":18,"items":["a","b"]}'`
- **主答案改写为 Hive**：`get_json_object(data, '$.name')`、`get_json_object(data, '$.age')`；数组展开：`LATERAL VIEW EXPLODE(SPLIT(get_json_object(data, '$.items'), ',')) t AS raw_item`（注明再 `regexp_replace` 去引号方括号）。SQLite 等价备注：照录 `json_extract` / `json_each`（1199-1207 行）。
- 延伸：`json_tuple(data, 'name', 'age')` 一次取多字段（比多次 get_json_object 少解析趟数）；嵌套路径 `$.a.b[0].c`。
- 面试追问：Q: get_json_object 和 json_tuple 选哪个？A: 单字段/嵌套用前者，平铺多字段用后者。Q: JSON 存表里好还是拆列好？A: 数仓规范一般落地为独立列/复杂类型（array/map/struct），脏 JSON 进 ETL。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `18`；`grep -c '<details>'` → `18`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add retention, explode/collect, date and JSON problems Q14-Q18"
```

---

### 任务 9：组 9 综合与建模（Q19-Q21）

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：写入三题**

**Q19（14_01 接雨水，manifest.py:1224-1258，难度5）**
- 表：`heights(height)`，示例 `(2,0,3)`——即柱高数组，行序即位置。
- 原答案方言修正后写入：两参 `MIN(lmax, rmax)` → `LEAST(lmax, rmax)`（两处，1249 与 1251 行），其余照录（1235-1251 行）。解析：每位储水 = `least(左滚动max, 右滚动max) - 高`（木桶效应）；右滚动 max 用 `order by idx desc` 反向帧；`row_number() over()` 给行编号把"数组题"转成"行题"。
- 延伸：算法题 SQL 化的一般套路——先找"逐行可计算的局部量"，再用窗口/聚合组合。
- 面试追问：Q: 为什么两端柱子不接水？A: least 中必有一侧是自身，差为 0（被 where 过滤）。Q: Hive 里多参取小？A: `least()`（SQLite/部分引擎是 `min()`）——方言坑。

**Q20（14_03 赛马问题，manifest.py:1271-1291，难度4）**
- 表：`race_result(horse, time)`，示例 `('甲',9.8),('乙',10.2),('丙',9.9)`
- 原答案照录（1283-1287 行）并解析：非等值 join `b.time < a.time` 找所有更快者，相关子查询 `min(time)` 收敛到"紧邻更快的那匹"。
- 延伸：**更优雅的窗口解法**（面试加分）：

```sql
SELECT horse, time,
       LAG(horse) OVER (ORDER BY time) AS faster_neighbor
FROM race_result;
```

- 同时指出原解法风险：非等值 join 笛卡尔放大（每行匹配数不定），大数据量禁用。
- 面试追问：Q: 非等值 join 的问题？A: 无法 hash 分桶，走 nested loop，数据放大。Q: 一条 SQL 顺手解决的话？A: lag(order by time) 一步到位。

**Q21（10_02 人事数仓表格设计，manifest.py:1007-1046，难度3）**
- 无需表结构展示，概念设计题。
- 原答案的建表语句照录（1018-1042 行），但改写为**带注释的建模讲解**：维度表（employee：谁，变化慢）vs 事实表（salary/attendance：发生了什么，按周期增长）；星型模型（事实居中连维度）vs 雪花（维度再规范化）；主键设计 `PRIMARY KEY (emp_id, month)` 支撑周期快照事实表。
- 延伸：拉链表处理员工维度缓慢变化（SCD）；为什么 emp_id 冗余在事实表（维度代理键）。
- 面试追问：Q: 星型和雪花怎么选？A: 查询性能（少 join）vs 冗余控制，数仓默认星型。Q: 员工调部门历史怎么留？A: 拉链表（start_date/end_date），呼应 Q3 的区间分段思想。

- [ ] **步骤 2：结构验收**

`grep -c '^### Q'` → `21`；`grep -c '<details>'` → `21`；`grep -c '</details>'` → `21`。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): add comprehensive problems Q19-Q21"
```

---

### 任务 10：全文一致性验收与收尾

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：删除 `<!-- APPEND -->` 标记**

文件中不应残留任何占位注释。运行：`grep -c 'APPEND' docs/sql-interview-review.md` → 预期 `0`（不为 0 则删除后重跑）。

- [ ] **步骤 2：结构核对**

```bash
grep -c '^### Q' docs/sql-interview-review.md          # 预期 21
grep -c '<details>' docs/sql-interview-review.md       # 预期 21
grep -c '</details>' docs/sql-interview-review.md      # 预期 21
grep -c '^## 组' docs/sql-interview-review.md          # 预期 9（Part 2 九个组标题）
for i in $(seq 1 21); do grep -q "^### Q$i\." docs/sql-interview-review.md || echo "MISSING Q$i"; done   # 预期无输出
grep -c '^## 1\.' docs/sql-interview-review.md        # 预期 5
```

- [ ] **步骤 3：题号引用一致性核对**

Part 1 表格中引用的 Q 号（Q1-Q20 分布在 1.1/1.2/1.3 表内）必须与 Part 2 实际题号一致。运行 `grep -o 'Q[0-9]\+' docs/sql-interview-review.md | sort -u`，人工比对：每题卡片规定的交叉引用（如 1.2 表"同时在线→Q8"、"接雨水→Q19"等）与实际标题对位；发现错位即修正。

- [ ] **步骤 4：覆盖映射核对（16 道吸收题）**

逐条确认归处内容真实存在（是实质讲解而非题号刷存在）：

```bash
grep -c '最大连续天数'  docs/sql-interview-review.md    # ≥1（01_02→Q1）
grep -c 'balance > 1000' docs/sql-interview-review.md   # ≥1（01_05→Q1）
grep -c 'test_xiaoming'  docs/sql-interview-review.md   # ≥1（01_06→Q3）
grep -c 'posexplode'     docs/sql-interview-review.md   # ≥1（02_02→Q4）
grep -c 'dr=2\|dr = 2'   docs/sql-interview-review.md   # ≥1（03_02→Q6）
grep -c '小时'            docs/sql-interview-review.md   # ≥1（04_03→Q8）
grep -c 'hour\|substr(event_time' docs/sql-interview-review.md  # ≥1（04_03/04_04→Q8）
grep -ic 'rank() over(partition by room_id' docs/sql-interview-review.md  # ≥1（04_05→Q8）
grep -ic 'count(distinct order_id)' docs/sql-interview-review.md            # ≥1（04_07→Q9）
grep -c 'min_so_far'     docs/sql-interview-review.md   # ≥1（04_08→Q7）
grep -ic 'map-side\|mapjoin\|map join' docs/sql-interview-review.md         # ≥1（06_03→Q13）
grep -c 'status_log'     docs/sql-interview-review.md   # ≥1（09_01→Q11）
grep -c '递归'            docs/sql-interview-review.md   # ≥1（10_01→1.5）
grep -c 'year(date)\|substr(date, 1, 4)' docs/sql-interview-review.md         # ≥1（11_01→1.4）
grep -c '(m-1)/3'        docs/sql-interview-review.md   # ≥1（11_02→Q17）
grep -c '连续问题'       docs/sql-interview-review.md   # ≥1（01_04→1.2）
```

任一条不满足 → 回对应任务补写实质内容后重跑。

- [ ] **步骤 5：方言残留核对**

```bash
grep -n 'INTERVAL' docs/sql-interview-review.md   # 预期：仅出现在"SQLite/MySQL 等价写法"备注行，主答案中不得出现
grep -n 'group_concat\|GROUP_CONCAT' docs/sql-interview-review.md  # 预期：仅 SQLite 备注行
grep -cn 'get_json_object' docs/sql-interview-review.md            # ≥1
```

- [ ] **步骤 6：渲染自检**

Read 全文一遍，检查：`<details>` 与 `</details>` 配对无嵌套错位；代码块 ``` 围栏配对；表格列数一致。发现问题直接修复。

- [ ] **步骤 7：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs(review): finalize handbook, verify cross-references and coverage"
```

---

## 自检记录

- **规格覆盖度**：规格 §3.1（速查五节）→ 任务 1-2；§3.2（21 题 9 组）→ 任务 3-9；§3.3（模板）→ 全局约定 4；§3.4（方言规范）→ 各题卡片改写指令 + 任务 10 步骤 5；§4（实现要点：分批写入、双题号标注、stub 不收录）→ 任务分解与卡片；§5（验收标准）→ 各任务验收步骤 + 任务 10。无遗漏。
- **占位符扫描**：各题卡片均给出具体来源行号、表结构、改写指令、延伸与追问条目；无"待定/类似任务 N"。
- **类型一致性**：Q 编号分配表（全局约定 6）与覆盖映射（全局约定 7）在任务 3-10 中引用一致；`docs/sql-interview-review.md` 路径全文统一。
