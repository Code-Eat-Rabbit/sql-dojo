# 页内 SQL 执行与自动判题 设计规格

- 日期：2026-10-01
- 状态：已批准（头脑风暴三节设计均经用户逐节确认）
- 后续：进入 writing-plans 编写实现计划

## 背景与目标

SQL Dojo 当前练习流程是"网页看题 → 在 DBeaver 等外部客户端写 SQL → 回网页自评打勾"，体验割裂且无判定反馈。本设计新增页内执行能力：在题目页面内编写 SQL、点击执行、查看结果，并与参考答案自动比对判题。

**目标：**

1. 一体化练习体验——题面、编写、执行、结果在同一页面完成
2. 自动判题——用户结果与参考答案比对，判对自动触发现有完成 + 星级自评流程

**已确认的产品决策：**

| 决策点 | 结论 |
|---|---|
| 架构 | 方案 A：扩展现有 FastAPI 后端，复用 PyMySQL 连接层，不新增服务 |
| 执行权限 | 只读查询（SELECT/SHOW/DESC/EXPLAIN/WITH）；DDL 题仍引导去外部工具 |
| 交互 | 「运行」与「提交答案」分开；判对触发 RatingModal + POST /api/progress |
| 编辑器 | CodeMirror 6（`@uiw/react-codemirror` + `@codemirror/lang-sql`） |
| 草稿持久化 | 存后端 progress.db，换设备不丢，重开题目回填 |

## 非目标

- 不支持 DDL/DML 的页内执行与判题（数据不可被用户改写，无需重置机制）
- 不做执行历史、多结果集并排展示
- 不做连接池改造（沿用每请求新建连接，单用户练习负载下无必要）
- 不支持多数据库方言（仅 MySQL 8）
- 不新增前端自动化测试设施（现状即无，手动验收）

## 架构

### 新增组件

| 单元 | 位置 | 职责 |
|---|---|---|
| `sql_executor.py` | `backend/` | 只读会话管理、语句白名单、语句拆分、超时、行数上限、错误归一化 |
| `grader.py` | `backend/` | 执行参考答案、结果归一化比对、差异摘要 |
| execute 路由 | `backend/routers/execute.py` | 运行/提交/草稿三个端点 |
| `SQLWorkspace` | `frontend/src/components/` | 编辑器 + 运行/提交按钮 + 结果表格 + 判题反馈 |
| `ResultTable` | `frontend/src/components/` | 通用结果表格（从 ProblemListPage 现有表格渲染代码抽出，两处共用） |
| `drafts` 表 | `progress.db` | 每题 SQL 草稿 |

### 复用清单

- `backend/database.py:18` `get_practice_connection(schema)`——PyMySQL 连接工厂（autocommit + DictCursor）
- `data_builder/smoke_test.py:37-46` `strip_comments()`/`statements()`——按 `;` 拆多语句
- smoke_test 的语句分类逻辑——判定题目 `gradable` 标记
- `frontend/src/api.ts` `fetchJson`、Vite `/api` 代理、ProblemListPage 现有表格渲染模式
- 现有 RatingModal 与 `/api/progress` 完成流程（不改）

### 数据流

```
运行：  编辑器 → POST /api/problems/{id}/execute {sql}
        → sql_executor 只读会话执行 → {columns, rows, rowCount, truncated, elapsedMs}

提交：  编辑器 → POST /api/problems/{id}/submit {sql}
        → 执行用户 SQL + 执行 reference_sql → grader 比对
        → {correct, diffSummary}
        → 判对后由前端拉起 RatingModal → POST /api/progress（现有端点）

草稿：  进入题目 GET /api/problems/{id}/draft 回填编辑器；
        输入 debounce 1s → PUT /api/problems/{id}/draft
```

## 后端设计

### 只读防护（三层）

1. **语句白名单预检**：拆分出的每条语句首个 token 必须属于 `{SELECT, WITH, SHOW, DESC, DESCRIBE, EXPLAIN}`，否则拒绝，不进数据库
2. **MySQL 会话级只读**：执行前 `SET SESSION TRANSACTION READ ONLY`——白名单被绕过时（如 `WITH ... DELETE`），写操作被 MySQL 以错误 1792 拒绝
3. **超时**：`SET SESSION max_execution_time = 5000`（毫秒），低效查询最多跑 5 秒

### 执行器行为（`sql_executor.py`）

- 连接复用 `get_practice_connection(schema)`，执行前设置上述两个会话变量
- 多语句：复用 smoke_test 的 `strip_comments`/`statements` 按 `;` 拆分，依次执行，返回最后一个带结果集的语句的列与行
- 行数上限：`fetchmany(501)`，超过 500 行置 `truncated: true`，仅返回 500 行
- SQL 总长度上限 64KB

### 判题语义（`grader.py`）

- **gradable 判定**：seed 时按语句分类标记——`reference_sql` 为纯查询语句的题目才可提交判题；DDL 题编辑器照常可用但无提交入口
- **比对规则**：列数相等 + 行多重集相等；默认顺序不敏感，manifest 每题可设 `ordered: true` 覆盖（排序题考点即顺序）
- **值归一化**：数值转 `Decimal` 精确比较、日期时间转 isoformat、NULL 统一表示，避免表示差异误判
- **判错反馈**：仅摘要不泄露答案——"列数不符（期望 3 列，实际 2 列）"、"缺 2 行 / 多 1 行"

### API 契约

```
POST /api/problems/{id}/execute   body: {sql}
  → 200 {columns: string[], rows: array[], rowCount: int, truncated: bool, elapsedMs: int}
  → 400 {"detail": {code, message}}   白名单拒绝 / 语法错误 / 只读违例
  → 503 {"detail": {code, message}}   MySQL 未启动或 schema 不存在

POST /api/problems/{id}/submit    body: {sql}
  → 200 {correct: bool, diffSummary: string | null}
  → 400 非查询题（不 gradable）
  （判对后的完成/自评走现有 /api/progress，本端点不改进度）

GET  /api/problems/{id}/draft     → 200 {sql: string}
PUT  /api/problems/{id}/draft     body: {sql} → 204
```

错误响应遵循 FastAPI 惯例使用 detail 字段包裹 {code, message}。

`rows` 为按列序的数组数组（非 DictCursor 的对象数组），与 `columns` 一一对应，判题比对也基于此。

### 错误转译

| MySQL 错误 | 用户提示 |
|---|---|
| 1792（只读违例） | "只允许查询语句" |
| 1064（语法错误） | "SQL 语法错误"+ MySQL 原始报文 |
| 3024（超时） | "执行超时（5s）" |

响应统一携带原始 error code 便于调试。

### progress.db 变更

- 新表 `drafts(problem_id TEXT PRIMARY KEY REFERENCES problems, sql_text TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL)`
- `problems` 表幂等加列（`ALTER TABLE ADD COLUMN`）：`gradable INTEGER NOT NULL DEFAULT 0`、`ordered INTEGER NOT NULL DEFAULT 0`
- `seed_problems()` 写入这两个字段；`data_builder/manifest.py` 的 `Problem` 增加 `ordered: bool = False` 字段

## 前端设计

ProblemListPage 右栏新增 `SQLWorkspace`，位于题面与"参考答案"折叠区之间；题面、表结构、样例数据、Hints、Mark as Complete 各区保持现状。

- **编辑器**：CodeMirror 6，MySQL 方言高亮；`Cmd/Ctrl+Enter` 触发运行
- **按钮**：「运行」（次级样式）、「提交答案」（主按钮，仅 gradable 题显示；DDL 题在该位置显示"此题为 DDL 题，请在 DBeaver 等外部工具完成后手动标记"提示文案）
- **结果区**：`ResultTable` 表格 + 状态栏（行数/耗时/截断提示）
- **判题反馈横幅**：判对（绿色，随即拉起现有 RatingModal）；判错（红色，显示 diffSummary，不展示参考答案）
- **草稿**：onChange debounce 1s 调 PUT draft；进入题目 GET draft 回填，首次为空串

## 边界与错误处理

- MySQL 未启动：编辑器上方离线提示条（含启动命令），运行/提交禁用
- 网络失败/后端 5xx：结果区错误横幅，可重试
- 提交判对但 progress POST 失败：提示"判定正确但保存进度失败"，不影响判对反馈
- 运行/提交期间按钮 loading，防重复点击

## 测试策略

- **后端 pytest**（uv dev 依赖补充 pytest）：`sql_executor` 白名单/拆句/行上限/错误映射；`grader` 比对规则（顺序敏感/不敏感、类型归一化、缺行多行）；端点测试连接真实 MySQL 容器（参考 smoke_test 真实执行模式）
- **前端**：手动验收，不新增测试设施
- **冒烟**：判题所依赖的 `reference_sql` 非空可执行已由现有 smoke_test 覆盖

## 验收标准

1. 打开任意查询题，编写 SQL 点「运行」，返回列/行/耗时
2. 结果与参考答案行集一致（默认乱序可过）时「提交答案」判对，拉起星级自评，进度表更新
3. 输入 INSERT/UPDATE/CREATE 等写语句被拒绝，提示友好
4. 刷新页面后草稿回填编辑器
5. DDL 题有「运行」入口、无「提交答案」入口
6. 停掉 MySQL 容器后页面显示离线提示，恢复后可执行

## 文档同步

README.md / README_zh.md 的练习流程段落小幅更新：页内执行为查询题主路径，外部工具（DBeaver）用于 DDL 题与自由探索。
