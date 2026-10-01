# 练习体验升级：分类知识点 + 进度重置 + 表名校正 设计规格

- 日期：2026-10-01
- 状态：已批准（头脑风暴三节设计均经用户逐节确认）
- 前置：页内 SQL 执行与自动判题已上线（见 2026-10-01-in-app-sql-execution-design.md）

## 背景与目标

用户验收页内执行功能后提出三项升级：

1. **分类知识点**：学习习惯是先看知识点再练习，每个分类开篇需展示"一般思路 + 需记忆的重要函数等"
2. **进度一键重置**：全部练习进度可一键清除重来
3. **表名校正**：消除 `test` 这类无含义表名，让数据集本身可读

**已确认的产品决策：**

| 决策点 | 结论 |
|---|---|
| 架构 | 方案 A：manifest 为单一事实源，全部顺现有模式 |
| 知识点位置 | 题目列表页顶部全宽可折叠卡片，默认展开 |
| 知识点内容 | AI 依据手册 Part 1 + 各分类题目生成 14 份初稿写入 manifest，用户校对 |
| 重置范围 | 只清 progress（状态/完成次数/掌握度/notes），drafts 草稿保留 |
| 重置入口 | 首页总进度条旁全局按钮 + 确认弹窗 |
| 表名范围 | 全部 6 个占位名（test、test_xiaoming、data_table×2、date_table、json_table）；metrics 保留 |
| 列名范围 | 仅 01 系两张表（test 的 id/date、test_xiaoming 的 id）；其余表列名不动 |

## 非目标

- 不做分类级重置入口（仅全局）
- 不做知识点编辑 UI（内容直接改 manifest）
- 不做 02/09/11/13 表的列名校正（后续可迭代）
- 不做旧表名兼容视图/别名（generate_data 每次重建 schema，无兼容需求）

## 功能 1：分类知识点

### 数据结构

`data_builder/manifest.py` 的 `Category` dataclass 追加：

```python
knowledge: str = ""   # 分类知识点（Markdown），进入分类后展示
```

14 个分类全部填写，每份固定三段结构：

```markdown
## 解题思路        ← 该类题的一般套路（2-4 条口诀式要点）
## 必背知识点      ← 重要函数/语法速查（表格：函数 | 语义 | 示例/备注）
## 易错点          ← 可选，从题目 hints 与手册追问清单提炼
```

内容来源：`docs/sql-interview-review.md` Part 1（窗口函数总览 16-32 行、题型口诀 34-56 行、JOIN 速查 58-69 行、日期函数 71-86 行、追问清单 88-96 行）+ 各分类题目与 hints，按分类重组。

### API（零 SQLite 变更）

- `GET /api/problems?category_id=`：响应中 `category` 对象补 `knowledge` 键——`backend/routers/problems.py:59-71` 由 manifest `get_category()` 构造处
- `GET /api/categories`：分类 dict 补 `knowledge` 键——`backend/routers/categories.py:34` 一带，与 name/db_file 同路径

### 前端

- `frontend/src/types.ts`：CategoryInfo 与 getProblems 的 category 类型补 `knowledge: string`
- `frontend/src/pages/ProblemListPage.tsx`：页面顶部（sidebar 与右侧面板之上）加全宽可折叠卡片：
  - 展开态：标题「📖 知识点：<分类名>」+ Markdown 渲染（复用 react-markdown，与题面同款 prose 样式）
  - 收起态：仅标题条（点击切换）；默认展开；切分类时重置为展开
  - 实现为独立组件 `KnowledgePanel`（含展开/收起状态），ProblemListPage 引用

## 功能 2：进度一键重置

### 后端

`backend/routers/progress.py` 新增：

```
POST /api/progress/reset
  → 200 {"reset": true, "cleared": <int>}   — cleared 为受影响题目数
```

实现：`get_progress_connection()` 事务内执行

```sql
DELETE FROM progress;
INSERT OR IGNORE INTO progress (problem_id) SELECT id FROM problems;
```

`drafts` 表与 `problems` 表不动。SQLite `sqlite3.connect` 默认隐式事务，DELETE + INSERT 后 `conn.commit()`。

### 前端

- `frontend/src/api.ts`：`resetProgress(): Promise<{reset: boolean; cleared: number}>`（POST）
- `frontend/src/pages/CategoryListPage.tsx`：`GlobalProgressBar` 右侧加「重置进度」次级按钮：
  - 点击弹 `ConfirmDialog`（新组件，复用 RatingModal 的 fixed 遮罩 + 白卡片模式），文案：“将清除**所有分类**的练习状态、完成次数、掌握度与笔记（不可恢复）。SQL 草稿会保留。是否继续？”
  - 确认 → `resetProgress()` → 成功：重载 `getCategories()`（进度归零）+ 顶部轻量成功提示（“已重置 N 题进度”）；失败：错误提示
- 已知边界（设计接受）：重置后打开任一题目，`get_problem` 既有副作用（problems.py:98-103）会把它标为 `in_progress`，不改

## 功能 3：表名与列名校正

### 映射表

| 旧表名 | schema | 用途 | 新表名 | 列变更 |
|---|---|---|---|---|
| `test` | 01 | 用户登录日期 | `login_log` | `id`→`user_id`、`date`→`login_date` |
| `test_xiaoming` | 01 | 用户日期区间 | `user_schedule` | `id`→`user_id`（其余保留） |
| `data_table` | 02 | 分组指标前后行转换 | `metric_readings` | 不动 |
| `data_table` | 09 | 分组值含缺口补 NULL | `sparse_readings` | 不动 |
| `date_table` | 11 | 多格式日期字符串 | `raw_dates` | 不动 |
| `json_table` | 13 | 用户画像 JSON 文档 | `user_profiles` | 不动（摆脱保留名反引号） |

### 改动面（一次改齐）

1. `data_builder/builders/`：01（两张表：建表/INSERT/print + 列名）、02、09、11、13（建表/INSERT/print）
2. `data_builder/manifest.py`：受影响题目的 `tables`、`reference_sql`、`description`（`test` 全库精确匹配 14 处：01_01/01_02/01_03；其余表名各 2-8 处：01_06、02_02、09_02、11_01-11_03、13_01）
3. `tests/backend/test_sql_executor_integration.py:20`、`tests/backend/test_execute_api.py:15,24`：对 `test` 表的引用改 `login_log`（含列名 `id`→`user_id`）
4. `docs/sql-interview-review.md`：约 30 处同步（test 10 处、test_xiaoming 2 处、data_table 5 处、date_table 2 处、json_table 5 处及相应列名）

### 生效与验证

- MySQL 侧零迁移：`generate_data.py:17-20` 每次启动 DROP 重建 schema，下次 `bash start.sh` 新表名自动生效
- 后端取表名全部经 manifest/problems 表（seed 重播），无硬编码
- `smoke_test.py` 按 manifest 逐题真实执行 reference_sql——新名错误立即 ✗，是主验证手段
- 既有 pytest 33 个测试兜底（改引用后须全绿）

## 测试策略

- **后端 pytest**：
  - knowledge：`GET /api/problems?category_id=01` 响应 category.knowledge 非空含 Markdown 结构；`GET /api/categories` 同
  - reset：seed + 完成若干题 + 写草稿 → reset → progress 全部 not_started、summary 归零、**drafts 仍在**、problems 表行数不变
  - 表名：既有 execute/submit 集成测试改用 `login_log`/`user_id` 后全绿
- **数据**：smoke_test 全量通过（表名列名改动的直接验证）
- **前端**：手动验收（无前端测试设施，沿用现状）

## 验收标准

1. 进入任一分类，顶部见知识点卡片，展开显示三段结构内容，可收起，刷新后仍默认展开
2. 14 个分类全部有知识点内容（无空卡）
3. 首页点「重置进度」→ 确认弹窗 → 确认后首页与各分类进度归零
4. 重置后打开题目，编辑器草稿仍在（回填）
5. `bash start.sh` 后，01 系表结构页显示 `login_log(user_id, login_date)`、`user_schedule`；02/09/11/13 显示 `metric_readings`/`sparse_readings`/`raw_dates`/`user_profiles`
6. 页内运行/判题在新表名下工作正常（用 01_01 跑通：编写 SQL → 运行 → 提交判对）
7. `uv run pytest` 全绿、`smoke_test` 失败为无
