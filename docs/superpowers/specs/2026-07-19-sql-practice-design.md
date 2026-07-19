# SQL 练习平台 — 设计规格

> 将「踏踏实实练SQL」文档转换为可使用的 SQL 练习项目（CodeTop 风格）

## 1. 项目概述

### 1.1 目标
- 将 71 道 SQL 面试题转化为配有真实数据的可练习项目
- 提供 Web 管理界面浏览题目、追踪进度
- 用户在 DBeaver 中连接 SQLite 库进行 SQL 练习
- 进度追踪：完成次数 + 手动评分 + 时间衰减自动计算掌握度

### 1.2 范围
- 包含 14 个大类全部 71 道题
- 数据构造：每道题精准反向生成可运行出结果的人造数据
- 前端：React 两个页面（专题列表 + 题目详情）
- 后端：FastAPI REST API，无鉴权（本地单用户）
- 单用户进度追踪（无多用户/登录）

### 1.3 不包含
- 在线 SQL 执行（练习在 DBeaver 中进行）
- 用户认证/多用户
- 题目编辑器/导入导出
- 移动端适配

---

## 2. 架构

### 2.1 方案选择
**方案 2：按专题分库** — 每个大类独立 SQLite 文件，DBeaver 连接对应库时只看到相关表。

### 2.2 技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| 数据构造 | Python (sqlite3, faker) | 分析 SQL 逻辑，反向生成练习数据 |
| 数据库 | SQLite（多文件） | 练习数据 + 进度数据 |
| 后端 | FastAPI + SQLAlchemy | REST API |
| 前端 | React 18 + Vite + Tailwind CSS | SPA 管理界面 |

### 2.3 目录结构

```
sql_practice/
├── data_builder/               # 数据构造引擎
│   ├── builders/               # 每道题一个 builder 脚本
│   │   ├── 01_01_continuous_login_3days.py
│   │   └── ...
│   ├── generate.py             # 一键生成全部数据
│   └── manifest.py             # manifest 定义（题目/专题/表映射）
├── databases/                  # 按专题输出的 SQLite 文件
│   ├── 01_continuous_login.db
│   ├── 02_window_lead_lag.db
│   ├── 03_window_rank.db
│   ├── 04_cumulative_agg.db
│   ├── 05_explode.db
│   ├── 06_joins.db
│   ├── 07_retention.db
│   ├── 08_expand_contract.db
│   ├── 09_merge_interval.db
│   ├── 10_hr_warehouse.db
│   ├── 11_date_processing.db
│   ├── 12_company_questions.db
│   ├── 13_json_parsing.db
│   ├── 14_fun_sql.db
│   ├── manifest.json           # 专题→库文件→题目 映射
│   └── progress.db             # 进度数据库（独立）
├── backend/                    # FastAPI
│   ├── main.py
│   ├── routers/
│   │   ├── categories.py
│   │   ├── problems.py
│   │   └── progress.py
│   ├── models/
│   │   ├── problem.py
│   │   └── progress.py
│   └── database.py             # 多库连接管理 + progress.db
├── frontend/                   # React (Vite)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── CategoryListPage.tsx
│   │   │   └── ProblemListPage.tsx
│   │   ├── components/
│   │   │   ├── GlobalProgressBar.tsx
│   │   │   ├── CategoryCard.tsx
│   │   │   ├── ProblemSidebar.tsx
│   │   │   ├── ProblemDetail.tsx
│   │   │   ├── TableSchema.tsx
│   │   │   ├── ReferenceAnswer.tsx
│   │   │   ├── ProgressPanel.tsx
│   │   │   └── DbConnectionInfo.tsx
│   │   └── api/               # fetch 封装
│   └── ...
└── docs/                       # 原始文档 + 设计文档
    └── superpowers/
        └── specs/
```

### 2.4 数据流

1. `data_builder/generate.py` → 读取 manifest → 运行各 builder → 输出 `.db` 到 `databases/`
2. FastAPI 启动时 → 读取 `databases/manifest.json` → 构建内存索引（category/problem/db 映射）
3. React → HTTP → FastAPI → 查询 progress.db + 读取练习库 schema → 返回 JSON
4. 用户 DBeaver → 连接 `databases/01_xxx.db` → 写 SQL → 查看结果
5. 用户 Web 前端 → 标记完成 → POST progress → FastAPI 写入 `progress.db`

---

## 3. 数据模型

### 3.1 进度数据库 `progress.db`

#### problems 表
| 列 | 类型 | 说明 |
|---|---|---|
| id | TEXT PK | 如 "01_01" |
| category_id | TEXT | 专题编号 |
| title | TEXT | 题目标题 |
| difficulty | INTEGER | 1-5 |
| db_path | TEXT | SQLite 文件相对路径 |
| table_names | TEXT | JSON 数组：该题所用表名 |
| description | TEXT | 题目描述（Markdown） |
| reference_sql | TEXT | 参考答案 |
| hints | TEXT | JSON 数组：提示列表 |
| tags | TEXT | JSON 数组：标签 |
| created_at | TIMESTAMP | |

#### progress 表
| 列 | 类型 | 说明 |
|---|---|---|
| problem_id | TEXT PK FK | |
| status | TEXT | not_started / completed（打开详情自动变为 in_progress，完成时变为 completed） |
| completed_count | INTEGER | 完成次数 |
| mastery_level | INTEGER | 手动评分 1-5 |
| last_practiced_at | TIMESTAMP | |
| notes | TEXT | 用户笔记 |
| updated_at | TIMESTAMP | |

### 3.2 manifest.json 结构

```json
{
  "categories": [
    {
      "id": "01",
      "name": "连续登陆",
      "db_file": "01_continuous_login.db",
      "order": 1
    }
  ],
  "problems": [
    {
      "id": "01_01",
      "category_id": "01",
      "title": "查询连续登陆3天以上的用户",
      "difficulty": 2,
      "builder": "builders/01_01_continuous_login_3days.py",
      "tags": ["字节面试题", "row_number", "连续"],
      "description": "题目描述...",
      "reference_sql": "SELECT ...",
      "tables": ["test"],
      "hints": ["提示1", "提示2"]
    }
  ]
}
```

### 3.3 掌握度计算规则

```
mastery_display = MAX(手动评分, 自动评级)

自动评级:
  completed_count >= 5 → 5
  completed_count >= 3 → 3
  completed_count >= 1 → 2
  completed_count = 0  → 0

时间衰减:
  last_practiced_at 距今 > 30天 → mastery_display = MAX(1, mastery_display - 1)
```

---

## 4. API 设计

### 4.1 端点列表

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/categories` | 专题列表（含进度统计） |
| GET | `/api/problems?category_id=01` | 题目列表（含每题进度） |
| GET | `/api/problems/01_01` | 单题详情 |
| GET | `/api/problems/01_01/tables` | 该题表结构 + 前5行预览 |
| POST | `/api/progress/01_01` | 标记完成 `{action: "complete", mastery: 1-5}` |
| PATCH | `/api/progress/01_01` | 更新评分/笔记 |
| GET | `/api/progress/summary` | 全局进度统计 |
| GET | `/api/databases/01/connect` | 返回 DBeaver 连接串 |

### 4.2 关键响应格式

**GET /api/problems?category_id=01**
```json
{
  "category": {"id": "01", "name": "连续登陆", "db_file": "01_continuous_login.db"},
  "problems": [
    {
      "id": "01_01",
      "title": "查询连续登陆3天以上的用户",
      "difficulty": 2,
      "tags": ["字节面试题", "row_number"],
      "progress": {
        "status": "completed",
        "completed_count": 3,
        "mastery_level": 4,
        "last_practiced_at": "2026-07-18T10:30:00"
      }
    }
  ],
  "stats": {"total": 7, "completed": 5, "avg_mastery": 3.2}
}
```

**GET /api/categories**
```json
{
  "categories": [
    {
      "id": "01",
      "name": "连续登陆",
      "db_file": "01_continuous_login.db",
      "order": 1,
      "stats": {"total": 7, "completed": 5, "avg_mastery": 3.2}
    }
  ],
  "global": {"total": 71, "completed": 48, "avg_mastery": 3.1}
}
```

**GET /api/problems/01_01/tables**
```json
{
  "tables": [
    {
      "name": "test",
      "columns": [
        {"name": "id", "type": "INTEGER"},
        {"name": "date", "type": "TEXT"}
      ],
      "sample_rows": [
        {"id": 1, "date": "2024-01-01"},
        {"id": 1, "date": "2024-01-02"}
      ],
      "row_count": 30
    }
  ],
  "db_connection": "sqlite:///绝对路径/01_continuous_login.db"
}
```

### 4.3 无鉴权
本地单用户，CORS 允许 `http://localhost:5173`。

---

## 5. 前端设计

### 5.1 页面：专题列表（首页）

路由：`/`

布局：
- 顶部：标题「踏踏实实练SQL」+ 全局进度条（完成数/总数 + 百分比）
- 主体：专题卡片网格（每行一个卡片）
  - 卡片内容：图标 + 专题名、题数、完成进度条（绿色）、平均掌握度（星级）
  - 点击进入该专题

### 5.2 页面：题目列表 + 详情

路由：`/category/:id`

布局：左右分栏
- **左侧（300px）**：题目列表
  - 每行：状态圆点（●完成/○未开始）、题目名、标签、难度星级、完成次数标记
  - 可滚动，点击切换右侧内容
- **右侧**：题目详情
  - 数据库连接信息区（db 文件名 + [复制连接串] 按钮）
  - 题目描述（Markdown 渲染）
  - 表结构区：表名 + 列定义表格 + 前 5 行数据预览
  - 参考答案区（默认折叠，点击展开）
  - 进度面板：掌握度星级（可交互评分）、完成次数、最后练习时间
  - [标记完成] 按钮（弹出评分弹窗）

### 5.3 交互细节

- 标记完成 → 弹出弹窗：星级评分（1-5）+ 可选笔记文本 → POST progress
- 评分星级可随时点击修改 → PATCH progress
- 复制连接串 → 一键复制 `sqlite:///绝对路径` → 粘贴到 DBeaver
- 进度数据乐观更新：先更新 UI，后台同步 API
- 参考答案默认折叠（避免偷看），点击展开/收起

### 5.4 组件树

```
App
├── CategoryListPage
│   ├── GlobalProgressBar
│   └── CategoryCard (×14)
└── ProblemListPage
    ├── DbConnectionInfo
    ├── ProblemSidebar
    │   └── ProblemItem (×N)
    └── ProblemDetail
        ├── MarkdownDescription
        ├── TableSchema (×N)
        ├── ReferenceAnswer (折叠)
        └── ProgressPanel
            ├── MasteryStars (交互)
            ├── CompletionStats
            └── CompleteButton → RatingModal
```

### 5.5 技术细节

- Vite + React 18 + TypeScript
- Tailwind CSS（样式）
- react-markdown（题目描述渲染）
- react-router-dom v6（路由）
- fetch + React Query 或 useSWR（数据请求 + 缓存）

---

## 6. 数据构造

### 6.1 构造原则

每道题独立一个 builder 脚本（`builders/XX_XX_title.py`），职责：
1. 分析该题 SQL 的期望结果（从文档中提取或从参考答案推断）
2. 反推需要哪些表、哪些列、多少行数据
3. 用 `sqlite3` + `random` 生成能产生非空查询结果的数据
4. 写入对应专题的 SQLite 库

### 6.2 构造策略

- **小数据集**：每表通常 10-50 行，足以验证 SQL 逻辑
- **确定性**：用固定 seed，保证每次生成的数据一致
- **覆盖边界**：包含 null、重复值、边界条件，让 SQL 有东西可处理
- **可运行**：每个 builder 生成后自带一条验证 SQL，确保数据能跑出参考答案的预期结果

### 6.3 生成流程

```python
# generate.py 伪代码
for problem in manifest.problems:
    builder = import_builder(problem.builder)
    db_path = manifest.get_db(problem.category_id)
    builder.build(db_path)  # 创建表 + 插入数据
    builder.validate(db_path)  # 跑参考答案，验证结果非空
```

---

## 7. 非功能需求

### 7.1 可维护性
- 新增题目只需：写 builder + 在 manifest 加一条记录
- 数据可变：`generate.py` 重新运行即可重建全部练习数据
- 进度与数据分离：重建数据不影响用户进度

### 7.2 性能
- 全量数据量小（总计 < 1000 行所有表），SQLite 无压力
- API 响应全部 HTTP 缓存（5min），练习数据不变
- 每个专题题目数 ≤ 10，无需分页

### 7.3 兼容性
- SQLite 使用标准 SQL 语法（Hive/Spark SQL 关键字做映射适配）
- DBeaver 支持 SQLite JDBC 驱动，开箱可用

---

## 8. 实现顺序

1. manifest.json + progress.db schema → 数据模型定稿
2. data_builder/builders/* → 数据构造（可并行开发）
3. backend（FastAPI）→ 先做 categories + problems API，再做 progress API
4. frontend（React）→ 专题列表 → 题目列表 → 详情页 → 进度交互
5. 端到端测试 → DBeaver 连接验证
