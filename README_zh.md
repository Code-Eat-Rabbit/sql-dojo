# 🥋 SQL Dojo（SQL 道场）

> CodeTop 风格的 SQL 面试练习平台。44 道真题，14 个专题，自动生成练习数据集。在 DBeaver 中实战，在浏览器中追踪进度。

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 这是什么？

SQL Dojo 将 **44 道真实 SQL 面试真题**（来自字节跳动、阿里巴巴、拼多多、集度、得物等公司）转化为可实战的练习环境。每道题都配有：

- **自动生成的练习数据** — 确定性、可复现，保证能跑出结果
- **按专题独立的 SQLite 数据库** — 在 DBeaver 中打开只看到相关表，零干扰
- **参考答案 + 分步讲解**
- **CodeTop 风格的 Web 管理后台** — 浏览题目、追踪进度、评分掌握度

## 🎯 和在线刷题平台有什么不同？

| | 传统在线 OJ | SQL Dojo |
|---|---|---|
| **练习环境** | 网页 SQL 编辑器 | **你本地的 DBeaver / DataGrip** |
| **数据可见性** | 隐藏测试用例 | **完整表数据，自由探索** |
| **进度追踪** | 通过/不通过计数 | **掌握度评分 + 完成次数 + 时间衰减** |
| **离线可用** | 需要网络 | **纯本地 — SQLite 文件在你硬盘上** |
| **可定制** | 固定题目 | **通过 manifest.py 自由添加题目** |

## 📊 专题覆盖

| # | 专题 | 题数 | 核心技能 |
|---|------|------|----------|
| 01 | 连续登陆 | 7 | `ROW_NUMBER`、日期运算、分组技巧 |
| 02 | 开窗函数 | 3 | `LAG`、`LEAD`、`FIRST_VALUE`、`LAST_VALUE` |
| 03 | 排序开窗 | 2 | `RANK`、`DENSE_RANK`、Top-N 查询 |
| 04 | 累计汇总 | 8 | `SUM() OVER`、同时在线人数、滚动累计 |
| 05 | 炸裂函数 | 1 | 区间合并、`EXPLODE` 模拟 |
| 06 | 关联应用 | 3 | 自关联、共同好友、千亿级优化 |
| 07 | 留存计算 | 1 | 七日留存、队列分析 |
| 08 | 数据展开与收缩 | 2 | 递归 CTE、`GROUP_CONCAT` |
| 09 | 合并区间 | 2 | 状态标记、缺失值填充 |
| 10 | 人事数仓 | 2 | 星型模型、维度建模 |
| 11 | 日期处理 | 3 | 格式转换、相对日期窗口 |
| 12 | 大厂原题 | 5 | 字节、阿里、拼多多、得物 |
| 13 | JSON 解析 | 1 | `JSON_EXTRACT`、`JSON_EACH` |
| 14 | 趣味 SQL | 4 | 接雨水、赛马问题、块熵计算 |

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- [DBeaver](https://dbeaver.io/)（或其他支持 SQLite 的客户端）

### 1. 克隆项目 & 生成数据

```bash
git clone https://github.com/Code-Eat-Rabbit/sql-dojo.git
cd sql-dojo

# 一键生成全部练习数据库
python3 data_builder/generate_data.py
```

这会在 `databases/` 目录下生成 14 个 SQLite 数据库，每个对应一个专题的表和数据。

### 2. 启动后端

```bash
pip install fastapi uvicorn
python3 -m uvicorn backend.main:app --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173` 即可使用。

### 4. 在 DBeaver 中练习

打开 DBeaver → 新建连接 → SQLite → 浏览选择 `databases/01_continuous_login.db`。写 SQL、验证结果，然后在 Web 后台标记该题完成。

每道题的详情页也显示了数据库连接串，支持一键复制。

## 🏗️ 架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  data_builder │────▶│  databases/  │◀────│   DBeaver    │
│  (Python)     │     │  (14 × .db)  │     │  (你写 SQL)  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │   backend/   │
                     │  (FastAPI)   │
                     └──────┬───────┘
                            │ REST API
                     ┌──────▼───────┐
                     │  frontend/   │
                     │  (React)     │
                     └──────────────┘
```

- **`data_builder/`** — 分析每道题的参考 SQL，反向生成能跑出结果的人造数据集
- **`databases/`** — 14 个独立 SQLite 文件 + `progress.db`（进度追踪）
- **`backend/`** — FastAPI REST API，提供题目元数据、表结构、进度管理
- **`frontend/`** — React SPA，两个页面：专题列表（首页）+ 题目列表（专题内）

## 📝 项目结构

```
sql-dojo/
├── data_builder/
│   ├── manifest.py              # 全部题目元数据（44 题，14 专题）
│   ├── generate_data.py         # 一键生成所有数据
│   └── builders/                # 每个专题一个 builder（01-14）
├── databases/                   # 生成的 SQLite 文件（gitignore）
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── database.py              # 多库连接管理 + progress.db
│   ├── models/schemas.py        # Pydantic 请求/响应模型
│   └── routers/
│       ├── categories.py        # GET /api/categories
│       ├── problems.py          # GET /api/problems, /:id, /:id/tables
│       ├── progress.py          # POST/PATCH /api/progress/:id, /summary
│       └── databases.py         # GET /api/databases/:id/connect
├── frontend/
│   └── src/
│       ├── types.ts             # TypeScript 类型定义
│       ├── api.ts               # API 封装
│       ├── App.tsx              # 路由配置
│       └── pages/
│           ├── CategoryListPage.tsx
│           └── ProblemListPage.tsx
└── docs/
    └── superpowers/
        ├── specs/               # 设计规格文档
        └── plans/               # 实现计划
```

## 🔧 自定义

### 新增题目

1. 在 `data_builder/manifest.py` 中添加 `Problem` 条目
2. 在对应专题的 builder 文件中添加建表和数据生成逻辑
3. 运行 `python3 data_builder/generate_data.py`

### 新增专题

1. 在 `data_builder/manifest.py` 中添加 `Category` 条目
2. 新建 `data_builder/builders/XX_topic_name.py`，实现 `build(conn)` 函数
3. 运行 `python3 data_builder/generate_data.py`

## 📄 License

MIT

---

> 📖 [English Docs](README.md)

## 🙏 致谢

题目内容改编自语兴的「踏踏实实练SQL」系列（[B站](https://space.bilibili.com/405479587) | [微信公众号：语数](https://ydata.vip)），仅供学习使用。
