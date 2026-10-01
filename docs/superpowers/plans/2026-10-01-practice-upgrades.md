# 练习体验升级（分类知识点 + 进度重置 + 表名列名校正）实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 每个分类在题目列表页顶部展示可折叠知识点卡片（manifest 为内容源）；新增全局进度一键重置（保留草稿）；将 6 个占位表名（含 01 系两张表的列名）校正为业务化命名。

**架构：** 方案 A——manifest 单一事实源：`Category.knowledge` Markdown 字段经既有 categories/problems API 透传（零 SQLite 变更）；`POST /api/progress/reset` 只清 progress 表并重建 not_started 行；表名按静态映射一次改齐（builders + manifest + tests + docs），靠 `generate_data` 每次 DROP 重建 schema 自动生效，smoke_test 全量真实执行为主验证。

**技术栈：** Python 3.11+ / FastAPI / pytest / React 19 / react-markdown / Tailwind 4 / MySQL 8（Docker）

**规格：** `docs/superpowers/specs/2026-10-01-practice-upgrades-design.md`

**前置条件（每个任务开始前确认）：**

- MySQL 容器在跑（`docker ps --filter name=sql-dojo-mysql`；不在则 `bash start.sh`）
- 在隔离 worktree 执行（using-git-worktrees；`uv sync` + `cd frontend && npm install`）
- 起点全量测试 33 passed

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `data_builder/manifest.py` | 修改 | Category 加 `knowledge` 字段 + 14 份知识点内容；表名/列名替换 |
| `backend/routers/categories.py` | 修改 | 分类 dict 补 knowledge 键 |
| `backend/routers/problems.py` | 修改 | list_problems 的 category dict 补 knowledge 键 |
| `backend/routers/progress.py` | 修改 | 新增 POST /progress/reset |
| `tests/backend/test_knowledge.py` | 创建 | knowledge 字段与内容测试 |
| `tests/backend/test_progress_reset.py` | 创建 | 重置端点测试（drafts 保留） |
| `tests/backend/test_sql_executor_integration.py` | 修改 | test→login_log、id→user_id |
| `tests/backend/test_execute_api.py` | 修改 | 同上 |
| `frontend/src/types.ts` | 修改 | CategoryInfo/getProblems 返回类型补 knowledge |
| `frontend/src/api.ts` | 修改 | resetProgress 函数 |
| `frontend/src/components/KnowledgePanel.tsx` | 创建 | 可折叠知识点卡片 |
| `frontend/src/components/ConfirmDialog.tsx` | 创建 | 通用确认弹窗 |
| `frontend/src/pages/ProblemListPage.tsx` | 修改 | 顶部集成 KnowledgePanel |
| `frontend/src/pages/CategoryListPage.tsx` | 修改 | 总进度条旁重置按钮 |
| `data_builder/builders/01_continuous_login.py` | 修改 | test→login_log（列 id/date→user_id/login_date）、test_xiaoming→user_schedule（id→user_id） |
| `data_builder/builders/02_window_lead_lag.py` | 修改 | data_table→metric_readings |
| `data_builder/builders/09_merge_interval.py` | 修改 | data_table→sparse_readings |
| `data_builder/builders/11_date_processing.py` | 修改 | date_table→raw_dates |
| `data_builder/builders/13_json_parsing.py` | 修改 | \`json_table\`→user_profiles |
| `docs/sql-interview-review.md` | 修改 | 约 30 处表名/列名同步 |

---

### 任务 1：Category.knowledge 字段 + API 透传

**文件：**
- 修改：`data_builder/manifest.py:39-54`（Category dataclass）
- 修改：`backend/routers/categories.py:38-48`
- 修改：`backend/routers/problems.py:65-77`
- 测试：`tests/backend/test_knowledge.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_knowledge.py`：

```python
"""knowledge 字段：API 透传（内容在任务 3 填充）"""


def test_problem_list_category_contains_knowledge(client):
    r = client.get("/api/problems?category_id=01")
    assert r.status_code == 200
    cat = r.json()["category"]
    assert "knowledge" in cat
    assert isinstance(cat["knowledge"], str)


def test_categories_contain_knowledge(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()["categories"]
    assert len(cats) == 14
    for c in cats:
        assert "knowledge" in c
        assert isinstance(c["knowledge"], str)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_knowledge.py -v`
预期：FAIL，`KeyError: 'knowledge'`

- [ ] **步骤 3：实现三处修改**

(a) `data_builder/manifest.py` Category dataclass（39-54 行），`problems` 字段后追加：

```python
    id: str
    name: str
    db_file: str           # "01_continuous_login.db"
    order: int
    problems: List[Problem]
    knowledge: str = ""    # 分类知识点（Markdown：解题思路/必背知识点/易错点）
```

(docstring 的 Attributes 段补一行：`knowledge: 分类知识点 Markdown，列表页顶部展示。`)

(b) `backend/routers/categories.py` 的 categories.append dict（38-48 行）补一行（与 `"order"` 并列）：

```python
            "order": cat.order if cat else 99,
            "knowledge": cat.knowledge if cat else "",
```

(c) `backend/routers/problems.py` list_problems 返回的 category dict（65-77 行）补一行：

```python
            "order": cat.order if cat else 0,
            "knowledge": cat.knowledge if cat else "",
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_knowledge.py -v && uv run pytest -q`
预期：2 passed；全量 35 passed

- [ ] **步骤 5：Commit**

```bash
git add data_builder/manifest.py backend/routers/categories.py backend/routers/problems.py tests/backend/test_knowledge.py
git commit -m "feat: expose category knowledge field via categories and problems APIs"
```

---

### 任务 2：前端 KnowledgePanel 组件

**文件：**
- 创建：`frontend/src/components/KnowledgePanel.tsx`
- 修改：`frontend/src/types.ts`
- 修改：`frontend/src/api.ts`
- 修改：`frontend/src/pages/ProblemListPage.tsx`

- [ ] **步骤 1：types.ts 与 api.ts 类型补充**

`frontend/src/types.ts` 的 `CategoryInfo` 补字段：

```typescript
export interface CategoryInfo {
  id: string
  name: string
  db_file: string
  order: number
  knowledge: string
  stats: { ... }   // 保持原样
}
```

`frontend/src/api.ts` 的 `getProblems` 返回类型中 category 补 `knowledge: string`：

```typescript
export function getProblems(categoryId: string): Promise<{
  category: { id: string; name: string; db_file: string; order: number; knowledge: string } | null
  problems: ProblemBrief[]
  stats: { total: number; completed: number }
}> {
```

- [ ] **步骤 2：创建 KnowledgePanel 组件**

`frontend/src/components/KnowledgePanel.tsx`：

```typescript
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function KnowledgePanel({
  title,
  knowledge,
}: {
  title: string
  knowledge: string
}) {
  const [open, setOpen] = useState(true)

  if (!knowledge) return null

  return (
    <div className="bg-white rounded-lg shadow-sm mb-4 flex-shrink-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 rounded-t-lg transition-colors"
      >
        <span className="text-sm font-semibold text-gray-700">📖 知识点：{title}</span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-3 border-t border-gray-100 prose prose-sm max-w-none text-sm text-gray-700">
          <ReactMarkdown>{knowledge}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
```

- [ ] **步骤 3：集成进 ProblemListPage**

(a) import 区补：

```typescript
import KnowledgePanel from '../components/KnowledgePanel'
```

(b) `categoryName` state（117 行附近）替换为整个 category 对象：

```typescript
  const [category, setCategory] = useState<{
    id: string; name: string; db_file: string; order: number; knowledge: string
  } | null>(null)
```

loadProblems 的 useEffect（135-142 行）中 `setCategoryName(data.category?.name || '')` 改为 `setCategory(data.category)`；页面中所有 `categoryName` 引用（253 行 `{categoryName || 'Problems'}`）改为 `{category?.name || 'Problems'}`。

(c) return 结构改为外层包 div，知识点卡片置于两栏之上（249 行 `<div className="flex gap-6 h-[calc(100vh-130px)]">` 处）：

```typescript
  return (
    <div>
      {category && <KnowledgePanel title={category.name} knowledge={category.knowledge} />}
      <div className="flex gap-6 h-[calc(100vh-130px)]">
        {/* ...原有 aside 与 section 不动... */}
      </div>
      {/* Rating Modal 原样保留在此层 */}
      <RatingModal open={showRating} onClose={() => setShowRating(false)} onSubmit={handleComplete} />
    </div>
  )
```

（注意：原 return 的闭合 `</div>` 与 RatingModal 位置相应调整；KnowledgePanel 默认展开，切分类时组件因 key 变化重建——用 `key={category.id}` 挂在 KnowledgePanel 上确保重置为展开态。）

- [ ] **步骤 4：构建与 lint 验证**

```bash
cd frontend && npm run build && npm run lint
```

预期：均退出 0（knowledge 此刻为空串，KnowledgePanel 返回 null 不渲染，任务 3 填内容后可见）。

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/types.ts frontend/src/api.ts frontend/src/components/KnowledgePanel.tsx frontend/src/pages/ProblemListPage.tsx
git commit -m "feat: collapsible knowledge panel on problem list page"
```

---

### 任务 3：14 个分类的知识点内容

**文件：**
- 修改：`data_builder/manifest.py`（14 个 Category 实例）
- 测试：`tests/backend/test_knowledge.py`（追加）

内容生产规则：每个 Category 构造加 `knowledge="""..."""` 关键字参数（`problems=[...]` 之后）。**三段固定结构**（`## 解题思路` / `## 必背知识点` / `## 易错点`，最后一段可省），必背知识点用表格（`函数/语法 | 语义 | 备注`）。内容依据下方各分类要点清单成文（要点齐全即可，表达可润色；口诀优先照抄 `docs/sql-interview-review.md` 1.1-1.5 的现成表述）。每份 30-60 行。

- [ ] **步骤 1：追加内容测试**

`tests/backend/test_knowledge.py` 追加：

```python
def test_all_categories_have_knowledge_content(client):
    cats = client.get("/api/categories").json()["categories"]
    for c in cats:
        assert "## 解题思路" in c["knowledge"], f"category {c['id']} 缺解题思路"
        assert "## 必背知识点" in c["knowledge"], f"category {c['id']} 缺必背知识点"
```

运行 `uv run pytest tests/backend/test_knowledge.py -v` 验证 FAIL（断言空串）。

- [ ] **步骤 2：撰写并填入 14 份内容**

各分类要点清单（函数名/口诀/公式必须出现）：

**01 连续登陆**：思路=①差值法口诀「去重 → `日期 - row_number()` 得分组键 → GROUP BY + HAVING 计数」②lag 法「lag 取前 N-1 个日期，datediff 全差 1 则连续」③自关联法「自关联 N 次，datediff=1 逐级衔接」④条件连续（连胜）「先筛满足条件的行 → 双 row_number 差值分组，或 lag+case 造断点 + sum() over 累加分段」。必背=row_number/rank/dense_rank 三者区别（1,2,3,4 / 1,2,2,4 / 1,2,2,3）、datediff(a,b) 是 a-b 天数、date_add/date_sub(d,n)（n 可负）、substr(date,1,10) 取日期部分。易错=排号前必须先去重（同日多次登录会打断连续）；NOT IN 子查询含 NULL 整体返回空。

**02 lead/lag**：思路=波峰波谷「lag 前值 + lead 后值 + case when 三比较」；环比变化率「lag 取前值 → (今-前)/前 → round」；前后列转换 lag/lead 当列。必背=lag(col,n,default)/lead(col,n,default)、first_value/last_value（last_value 默认帧不含后续行，易错）、窗口 `OVER(PARTITION BY ... ORDER BY ...)` 结构。

**03 排序开窗**：思路=TopN「row_number 并列也分先后，去重取一名」；第 N 高「dense_rank() over(partition by ... order by ... desc) 取 = N」。必背=三函数区别表（同 01）、要名次跳号用 rank、不跳号/取第 N 高用 dense_rank、TopN 去重用 row_number。

**04 累计汇总**：思路=「sum() over 加 ORDER BY = 累计；不加 = 分组总量」；同时在线「进 +1 / 出 -1 → union all → sum() over 累加 → max 取峰值」（必须 union all 不能 union）；首次达标「累计后 where 筛 + min(日期)」。必背=sum/min/max/avg/count(col) OVER(...)、帧语法 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW、默认帧规则（有 ORDER BY 为 RANGE 到当前行；无则全组）、ROWS vs RANGE 差异。

**05 炸裂函数**：思路=行转列（一行变多行）：Hive 用 lateral view explode(split(col,','))；MySQL 8 用 JSON_TABLE 或递归 CTE。必背=split(s,',')、explode、JSON_TABLE 语法骨架（见 13 系）、lateral view 位置（from 之后 where 之前）。

**06 joins**：思路=全称量词「每科都>60 = 双重否定：not in（存在不及格的学生），或 group by + having min(score) > 60」；相互关注「自关联 a.from=b.to and a.to=b.from，或 union all 双向 + having count>=2」。必背=join 类型表（inner/left/full outer/自关联/非等值）、left join 保分母不丢（留存题关键）、非等值 join 会数据放大注意行数。易错=NOT IN + NULL 陷阱（规避：NOT EXISTS 或子查询加 WHERE col IS NOT NULL）。

**07 留存**：思路=「min(date) 定首活 → left join 第 N 天活跃 → count(distinct) 分子分母」。必背=left join 保分母、count(distinct uid)、date_add(首活日, N)。易错=分母用 left join 不能用 inner join。

**08 展开收缩**：思路=行转列见 05 系；列转行（多行并一行）：MySQL 8 用 GROUP_CONCAT(col SEPARATOR ',')，Hive 用 concat_ws(',', collect_list(col))。必背=GROUP_CONCAT SEPARATOR 语法、concat_ws 跳过 NULL、collect_list/collect_set 区别（保重/去重）。

**09 合并区间**：思路=区间断点分段「lag(end) 与当前 start 比较 → case 造 0/1 → sum() over 累加成组号 → min(start), max(end)」；状态标记「lead 取下一行时间作为当前状态结束时间」；缺失值填充「相关子查询取最近非空前值（forward fill）」。必背=lag/lead 在区间题的用法、SUM 标志累加分段法。

**10 人事数仓**：思路=星型/雪花建模（事实表 + 维度表：employee 维度、salary/attendance 事实）；递归 vs 开窗辨析「先看能否用 row_number/lag + 聚合开窗的分段子问题套路；真需要逐行传递状态才递归」。必背=事实表/维度表概念、星型 vs 雪花、缓慢变化维（SCD）一句话。

**11 日期处理**：思路=「substr + 算术组合」。必背表=year: substr(date,1,4)；mm: substr(date,6,2)；季度公式 (month-1) DIV 3 + 1（ concat(substr(date,1,4),'Q',...) ）；半年 (m-1) DIV 6+1；ytm: substr(date,1,7)；last12m: date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)；last30d/60d/90d/180d 同理；last_day(d) 月末。易错=Hive 整除用 div、date_add(d,n) 不是 INTERVAL 语法。

**12 大厂原题（stub）**：思路=题目补充中；给面试通用追问清单：窗口函数 vs GROUP BY（压缩为每组一行 vs 保留每行附加计算列）、COUNT(DISTINCT) 数据倾斜（先 group by 预聚合/两阶段）、千亿级 join 优化（小表广播 mapjoin/分桶/Bloom filter）、union all vs union。必背=以上四条口诀。

**13 JSON 解析**：思路=MySQL 8 JSON 函数：字段提取 JSON_EXTRACT(col,'$.key')；数组展开 JSON_TABLE（对应 Hive lateral view explode）。必背=JSON_EXTRACT 路径语法 '$.key'、JSON_TABLE 骨架 `JSON_TABLE(col, '$.items[*]' COLUMNS (item VARCHAR(64) PATH '$'))`、JSON_TABLE 是 MySQL 8 表函数需逗号连用。易错=表名列名不要叫 json_table（撞保留函数名）。

**14 趣味 SQL**：思路=接雨水「每位储水 = least(左滚动max, 右滚动max) - 当前高，两侧 max() over 求出」；找相邻更快者「非等值 join b.time < a.time + 取 min；更优 lag() over(order by time)」。必背=max() over 滚动极值、least/greatest、非等值 join 的数据放大。

- [ ] **步骤 3：运行测试验证通过**

运行：`uv run pytest tests/backend/test_knowledge.py -v && uv run pytest -q`
预期：3 passed；全量 36 passed

- [ ] **步骤 4：Commit**

```bash
git add data_builder/manifest.py tests/backend/test_knowledge.py
git commit -m "docs: knowledge content for all 14 categories"
```

---

### 任务 4：POST /api/progress/reset 端点

**文件：**
- 修改：`backend/routers/progress.py`（末尾追加）
- 测试：`tests/backend/test_progress_reset.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_progress_reset.py`：

```python
"""进度一键重置：清 progress、保留 drafts、problems 不动"""


def test_reset_clears_progress_keeps_drafts(client):
    # 造状态：完成两题 + 写一条草稿
    assert client.post(
        "/api/progress/01_01", json={"action": "complete", "mastery": 4}
    ).status_code == 200
    assert client.post(
        "/api/progress/01_02", json={"action": "complete", "mastery": 3}
    ).status_code == 200
    assert client.put(
        "/api/problems/01_01/draft", json={"sql": "SELECT 1"}
    ).status_code == 204

    r = client.post("/api/progress/reset")
    assert r.status_code == 200
    assert r.json() == {"reset": True, "cleared": 44}

    # 进度归零（summary 无副作用，先于 detail 调用）
    summary = client.get("/api/progress/summary").json()
    assert summary["completed"] == 0
    assert summary["in_progress"] == 0
    assert summary["not_started"] == summary["total"]

    # 草稿保留
    assert client.get("/api/problems/01_01/draft").json() == {"sql": "SELECT 1"}
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_progress_reset.py -v`
预期：FAIL，404（路由不存在）

- [ ] **步骤 3：实现端点**

`backend/routers/progress.py` 文件末尾追加：

```python
@router.post("/progress/reset")
def reset_progress():
    """Reset all practice progress; drafts and problems are preserved"""
    conn = get_progress_connection()
    try:
        cleared = conn.execute(
            "SELECT COUNT(*) AS n FROM progress"
        ).fetchone()["n"]
        conn.execute("DELETE FROM progress")
        conn.execute(
            "INSERT OR IGNORE INTO progress (problem_id) SELECT id FROM problems"
        )
        conn.commit()
    finally:
        conn.close()
    return {"reset": True, "cleared": cleared}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_progress_reset.py -v && uv run pytest -q`
预期：1 passed；全量 37 passed

- [ ] **步骤 5：Commit**

```bash
git add backend/routers/progress.py tests/backend/test_progress_reset.py
git commit -m "feat: global progress reset endpoint preserving drafts"
```

---

### 任务 5：前端重置按钮与确认弹窗

**文件：**
- 创建：`frontend/src/components/ConfirmDialog.tsx`
- 修改：`frontend/src/api.ts`
- 修改：`frontend/src/pages/CategoryListPage.tsx`

- [ ] **步骤 1：api.ts 追加**

```typescript
export function resetProgress(): Promise<{ reset: boolean; cleared: number }> {
  return fetchJson(`${BASE}/progress/reset`, { method: 'POST' })
}
```

- [ ] **步骤 2：创建 ConfirmDialog 组件**

`frontend/src/components/ConfirmDialog.tsx`（复用 RatingModal 的遮罩 + 白卡片模式）：

```typescript
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmText = '确认',
  busy = false,
  onConfirm,
  onClose,
}: {
  open: boolean
  title: string
  message: string
  confirmText?: string
  busy?: boolean
  onConfirm: () => void
  onClose: () => void
}) {
  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">{title}</h3>
        <p className="text-sm text-gray-600 mb-6 whitespace-pre-line">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            disabled={busy}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {busy ? '处理中…' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **步骤 3：集成进 CategoryListPage**

(a) import 补 `ConfirmDialog` 与 `resetProgress`；`GlobalProgressBar`（6-24 行）加 `actions` prop，标题行（11-15 行）改为：

```typescript
function GlobalProgressBar({
  total,
  completed,
  actions,
}: {
  total: number
  completed: number
  actions?: React.ReactNode
}) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold text-gray-800">Overall Progress</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            {completed} / {total} completed ({pct}%)
          </span>
          {actions}
        </div>
      </div>
      {/* 进度条 div 原样保留 */}
```

(b) `CategoryListPage` 组件加状态与处理函数（79-89 行 state 区 + 新函数）：

```typescript
  const [showReset, setShowReset] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [resetNotice, setResetNotice] = useState<string | null>(null)

  const loadCategories = () => {
    getCategories()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  const handleReset = async () => {
    setResetting(true)
    try {
      const r = await resetProgress()
      setShowReset(false)
      setResetNotice(`已重置 ${r.cleared} 题进度`)
      setTimeout(() => setResetNotice(null), 3000)
      loadCategories()
    } catch (err) {
      setShowReset(false)
      setError(err instanceof Error ? err.message : '重置失败')
    } finally {
      setResetting(false)
    }
  }
```

（原 useEffect 里的加载逻辑改调 `loadCategories()`，保持仅挂载时执行一次。）

(c) 渲染区（109-114 行 GlobalProgressBar 处）：

```typescript
      <GlobalProgressBar
        total={data.global_stats.total}
        completed={data.global_stats.completed}
        actions={
          <button
            onClick={() => setShowReset(true)}
            className="px-3 py-1.5 text-xs border border-gray-300 text-gray-600 rounded-md hover:bg-gray-100 transition-colors"
          >
            重置进度
          </button>
        }
      />

      {resetNotice && (
        <div className="bg-green-50 border border-green-200 text-green-700 rounded-lg p-3 mb-4 text-sm">
          {resetNotice}
        </div>
      )}
```

(d) 组件末尾（`</div>` 闭合前）加：

```typescript
      <ConfirmDialog
        open={showReset}
        title="重置全部进度"
        message={'将清除所有分类的练习状态、完成次数、掌握度与笔记（不可恢复）。\nSQL 草稿会保留。\n是否继续？'}
        confirmText="重置"
        busy={resetting}
        onConfirm={handleReset}
        onClose={() => setShowReset(false)}
      />
```

- [ ] **步骤 4：构建与 lint 验证**

```bash
cd frontend && npm run build && npm run lint
```

预期：均退出 0。

- [ ] **步骤 5：Commit**

```bash
git add frontend/src/api.ts frontend/src/components/ConfirmDialog.tsx frontend/src/pages/CategoryListPage.tsx
git commit -m "feat: global progress reset with confirmation dialog"
```

---

### 任务 6：builders 表名/列名重命名

**文件：**
- 修改：`data_builder/builders/01_continuous_login.py`
- 修改：`data_builder/builders/02_window_lead_lag.py`
- 修改：`data_builder/builders/09_merge_interval.py`
- 修改：`data_builder/builders/11_date_processing.py`
- 修改：`data_builder/builders/13_json_parsing.py`

- [ ] **步骤 1：重写 01 builder 的两张表**

`data_builder/builders/01_continuous_login.py`：

(a) test 表（9-36 行）整段替换为：

```python
    # ===== login_log 表：用户登录记录 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS login_log (
            user_id INTEGER,
            login_date VARCHAR(20)
        )
    """)

    # 生成数据：5 个用户，每人登录 8-15 天
    random.seed(42)
    login_data = []
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
            login_data.append((user_id, d))

    cur.executemany(
        "INSERT INTO login_log (user_id, login_date) VALUES (%s, %s)", login_data
    )
```

(b) test_xiaoming 表（60-81 行）整段替换为：

```python
    # ===== user_schedule 表：日期区间（拓展2） =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_schedule (
            user_id INTEGER,
            name VARCHAR(128),
            start_date VARCHAR(10),
            end_date VARCHAR(10)
        )
    """)

    schedule_data = [
        (1, "小明", "2024-01-01", "2024-01-05"),
        (1, "小明", "2024-01-06", "2024-01-10"),
        (1, "小明", "2024-01-15", "2024-01-20"),
        (2, "小红", "2024-02-01", "2024-02-03"),
        (2, "小红", "2024-02-03", "2024-02-07"),
        (2, "小红", "2024-02-10", "2024-02-12"),
    ]
    cur.executemany(
        "INSERT INTO user_schedule (user_id, name, start_date, end_date) "
        "VALUES (%s, %s, %s, %s)",
        schedule_data
    )
```

(c) print 行（102-105 行）改为：

```python
    print(f"     login_log: {len(login_data)} rows")
    print(f"     account: {len(account_data)} rows")
    print(f"     user_schedule: {len(schedule_data)} rows")
    print(f"     games: {len(game_data)} rows")
```

- [ ] **步骤 2：其余四个 builder 精确替换**

规则（先 `grep -n '<旧名>' <文件>` 列出全部出现点，确认无遗漏后逐一替换；**只动表名，不动列名**）：

- `02_window_lead_lag.py`：`data_table` → `metric_readings`（建表 31 行、INSERT INTO、变量 `data_table_data`→`metric_readings_data`、print 行）
- `09_merge_interval.py`：`data_table` → `sparse_readings`（同上四处）
- `11_date_processing.py`：`date_table` → `raw_dates`（建表、INSERT INTO、print；列名 `date` 保留，变量 `date_data` 保留）
- `13_json_parsing.py`：`` `json_table` `` → `user_profiles`（建表去反引号、INSERT INTO 去反引号、print；变量 `json_data` 保留）

替换后逐文件验证：

```bash
grep -nE '\btest\b|test_xiaoming|data_table|date_table|json_table' data_builder/builders/*.py
```

预期：无输出。

- [ ] **步骤 3：重新生成数据验证**

```bash
uv run python data_builder/generate_data.py 2>&1 | grep -E 'login_log|user_schedule|metric_readings|sparse_readings|raw_dates|user_profiles|test'
```

预期输出包含 6 个新表名及行数（login_log 46、user_schedule 6 与旧 test/test_xiaoming 一致——数据生成逻辑未动），且不含旧名。

- [ ] **步骤 4：Commit**

```bash
git add data_builder/builders/
git commit -m "refactor: rename placeholder tables to business names in builders"
```

---

### 任务 7：manifest 与测试同步新表名

**文件：**
- 修改：`data_builder/manifest.py`（受影响 10 题）
- 修改：`tests/backend/test_sql_executor_integration.py`
- 修改：`tests/backend/test_execute_api.py`

- [ ] **步骤 1：manifest 精确替换**

替换规则（词边界精确替换；`date1`/`day_cnt` 等别名不会被 `\bdate\b`/`\bid\b` 误伤）：

| 题目 | 替换 |
|---|---|
| 01_01/01_02/01_03（description + reference_sql + tables） | `test`→`login_log`；`\bid\b`→`user_id`；`\bdate\b`→`login_date` |
| 01_06（reference_sql + tables） | `test_xiaoming`→`user_schedule`；`\bid\b`→`user_id`（`NAME`/start_date/end_date 保留） |
| 02_02（reference_sql + tables） | `data_table`→`metric_readings`（列 id/date/value 保留） |
| 09_02（reference_sql + tables） | `data_table`→`sparse_readings`（列与 t1/t2 别名保留） |
| 11_01/11_02/11_03（reference_sql + tables） | `date_table`→`raw_dates`（列 `date` 保留） |
| 13_01（reference_sql + tables） | `` `json_table` ``→`user_profiles`（去反引号，两处） |

01_01 description 的替换示例（84 行）：

```
English: Given a user login table `login_log` with fields `user_id` (user ID) and `login_date` (login date), ...
```

01_01 reference_sql 替换后首段（示意，全文件同规则）：

```sql
-- 步骤一：去重
SELECT user_id, substr(login_date, 1, 10) AS login_date
FROM login_log
GROUP BY user_id, substr(login_date, 1, 10);
```

验证：

```bash
grep -nE '\btest\b|test_xiaoming|FROM data_table|JOIN data_table|date_table|`json_table`' data_builder/manifest.py
```

预期：无输出。

- [ ] **步骤 2：测试文件同步**

`tests/backend/test_sql_executor_integration.py`：

- 20 行：`SELECT id FROM test LIMIT 3` → `SELECT user_id FROM login_log LIMIT 3`
- 21 行：`r["columns"] == ["id"]` → `r["columns"] == ["user_id"]`
- WITH...UPDATE 用例：`UPDATE test SET id = id` → `UPDATE login_log SET user_id = user_id`

`tests/backend/test_execute_api.py`：

- 15 行：`SELECT id FROM test LIMIT 3` → `SELECT user_id FROM login_log LIMIT 3`
- 17 行：`data["columns"] == ["id"]` → `data["columns"] == ["user_id"]`
- 24 行：`DELETE FROM test` → `DELETE FROM login_log`

- [ ] **步骤 3：全量验证**

```bash
uv run pytest -q
uv run python data_builder/smoke_test.py
```

预期：37 passed；smoke 全部 ✓、失败为无（smoke 按新 manifest SQL 在任务 6 已重建的 schema 上真实执行，表名列名错误会立即 ✗）。

- [ ] **步骤 4：Commit**

```bash
git add data_builder/manifest.py tests/backend/test_sql_executor_integration.py tests/backend/test_execute_api.py
git commit -m "refactor: align manifest reference SQL and tests with renamed tables"
```

---

### 任务 8：docs 手册同步

**文件：**
- 修改：`docs/sql-interview-review.md`

- [ ] **步骤 1：按规则替换**

应用与任务 7 相同的替换规则：`test`→`login_log` + `\bid\b`→`user_id` + `\bdate\b`→`login_date`（仅 Q1/Q2 题面与 SQL 处，约 10 处）、`test_xiaoming`→`user_schedule`（含 `\bid\b`→`user_id`，2 处）、`data_table`→`metric_readings`/`sparse_readings`（按上下文对应 02/09 题，5 处）、`date_table`→`raw_dates`（2 处，列 `date` 保留）、`` `json_table` ``→`user_profiles`（5 处）。

- [ ] **步骤 2：人工核验残留**

```bash
grep -nE '\btest\b|test_xiaoming|data_table|date_table|json_table' docs/sql-interview-review.md
```

对每条残留逐个人工判断：英文单词义（如 "test cases"）可保留；表引用义必须替换。

- [ ] **步骤 3：Commit**

```bash
git add docs/sql-interview-review.md
git commit -m "docs: sync handbook table names with renamed schemas"
```

---

### 任务 9：收尾回归与迁移

**文件：**
- 无代码改动（验证与数据迁移）

- [ ] **步骤 1：全量回归**

```bash
uv run pytest -q
uv run python data_builder/smoke_test.py
cd frontend && npm run build && npm run lint
```

预期：37 passed；smoke 失败为无；build/lint 退出 0。

- [ ] **步骤 2：worktree 本地 seed（幂等迁移验证）**

```bash
uv run python -c "from backend.database import init_progress_db, seed_problems; init_progress_db(); seed_problems(); print('ok')"
git status --short
```

预期：输出 ok；无新跟踪文件（databases/*.db 已忽略）。

- [ ] **步骤 3：手动验收（合并回主分支并 bash start.sh 后执行）**

1. 进入任一分类：顶部知识点卡片默认展开、三段结构、可收起；14 个分类全部有内容
2. 首页「重置进度」→ 确认弹窗（含影响范围与草稿保留说明）→ 确认后进度条归零、出现绿色提示
3. 重置后打开题目：编辑器草稿仍在
4. 01 系表结构页显示 `login_log(user_id, login_date)`、`user_schedule(user_id, name, ...)`
5. 01_01 页内写 SQL（对新表名）→ 运行出结果 → 提交判对
6. 02/09/11/13 表结构页显示 `metric_readings`/`sparse_readings`/`raw_dates`/`user_profiles`

- [ ] **步骤 4：Commit（如无改动则跳过）**

---

## 自检记录

- **规格覆盖度：** knowledge 字段+API（任务 1）、KnowledgePanel 卡片（任务 2）、14 份内容（任务 3）、reset 端点含 drafts 保留（任务 4）、全局按钮+确认弹窗（任务 5）、builders 六表重命名含 01 列名（任务 6）、manifest+tests 同步（任务 7）、docs 约 30 处（任务 8）、回归+seed+验收（任务 9）——规格各节均有对应任务；验收标准 1-7 分别由任务 3/5/5/9/6+9/7+9/9 覆盖。
- **占位符扫描：** 无"待定/TODO/类似任务 N"；知识点内容给出逐分类要点清单（函数/口诀/公式具体到字符），SQL 替换给出精确规则与示例。
- **类型一致性：** `Category.knowledge: str = ""`（任务 1 定义，任务 3 填充）；前端 `knowledge: string` 在 types/api（任务 2）与 KnowledgePanel props（任务 2）、ProblemListPage state（任务 2）一致；`resetProgress(): Promise<{reset, cleared}>`（任务 5）与端点返回（任务 4）一致；表名映射在任务 6/7/8 三处使用同一张映射表。
