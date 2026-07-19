# 🥋 SQL Dojo

> A CodeTop-style SQL interview practice platform. 44 real problems, 14 topics, auto-generated datasets. Practice in DBeaver, track progress in browser.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📖 What is SQL Dojo?

SQL Dojo transforms a curated collection of **44 real SQL interview problems** (from companies like ByteDance, Alibaba, PDD, Jidu, and Dewu) into a fully interactive practice environment. Each problem comes with:

- **Auto-generated practice data** — deterministic, reproducible, guaranteed to produce results
- **Per-topic SQLite databases** — open any topic in DBeaver and see only the relevant tables
- **Reference solutions with step-by-step explanations**
- **A CodeTop-style web dashboard** — browse problems, track progress, rate your mastery

## 🎯 Why SQL Dojo?

| | Typical online judge | SQL Dojo |
|---|---|---|
| **Practice environment** | Web-based SQL editor | **Your own DBeaver / DataGrip** |
| **Data visibility** | Hidden test cases | **Full table access, explore data freely** |
| **Progress tracking** | Pass/fail counter | **Mastery rating + completion count + time decay** |
| **Offline capability** | Requires internet | **Fully local — SQLite files on your disk** |
| **Customizable** | Fixed problems | **Add your own problems via manifest.py** |

## 📊 Topics Covered

| # | Topic | Problems | Key Skills |
|---|-------|----------|------------|
| 01 | 连续登陆 / Continuous Login | 7 | `ROW_NUMBER`, date arithmetic, grouping |
| 02 | 开窗函数 / Window Functions | 3 | `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE` |
| 03 | 排序开窗 / Window Ranking | 2 | `RANK`, `DENSE_RANK`, top-N queries |
| 04 | 累计汇总 / Cumulative Aggregation | 8 | `SUM() OVER`, concurrent users, running totals |
| 05 | 炸裂函数 / Explode Functions | 1 | Interval merging, `EXPLODE` simulation |
| 06 | 关联应用 / Join Applications | 3 | Self-joins, mutual friends, billion-row optimization |
| 07 | 留存计算 / Retention Analysis | 1 | 7-day retention, cohort analysis |
| 08 | 数据展开与收缩 / Pivot & Unpivot | 2 | Recursive CTE, `GROUP_CONCAT` |
| 09 | 合并区间 / Interval Merging | 2 | State tracking, forward fill |
| 10 | 人事数仓 / HR Data Warehouse | 2 | Star schema, dimension modeling |
| 11 | 日期处理 / Date Processing | 3 | Format conversion, relative date windows |
| 12 | 大厂原题 / Company Questions | 5 | ByteDance, Alibaba, PDD, Dewu |
| 13 | JSON 解析 / JSON Parsing | 1 | `JSON_EXTRACT`, `JSON_EACH` |
| 14 | 趣味 SQL / Fun SQL | 4 | Trapping rain water, horse racing, block entropy |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [DBeaver](https://dbeaver.io/) (or any SQLite-compatible client)

### 1. Clone & Generate Data

```bash
git clone https://github.com/Code-Eat-Rabbit/sql-dojo.git
cd sql-dojo

# Generate all practice databases
python3 data_builder/generate_data.py
```

This creates 14 SQLite databases under `databases/`, each containing the tables and data for one topic.

### 2. Start Backend

```bash
pip install fastapi uvicorn
python3 -m uvicorn backend.main:app --port 8000
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### 4. Connect DBeaver

Open DBeaver → New Connection → SQLite → browse to `databases/01_continuous_login.db`. Write SQL, verify your results, then mark the problem as complete in the web dashboard.

The connection string is also displayed on each problem's detail page — click to copy.

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  data_builder │────▶│  databases/  │◀────│   DBeaver    │
│  (Python)     │     │  (14 × .db)  │     │  (your SQL)  │
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

- **`data_builder/`** — Python scripts that analyze each problem's reference SQL and generate deterministic datasets guaranteed to produce non-empty results
- **`databases/`** — 14 per-topic SQLite files + `progress.db` for tracking
- **`backend/`** — FastAPI REST API serving problem metadata, table schemas, and progress operations
- **`frontend/`** — React SPA with two pages: topic list (home) and problem list + detail (per topic)

## 📝 Project Structure

```
sql-dojo/
├── data_builder/
│   ├── manifest.py              # All problem metadata (44 problems, 14 categories)
│   ├── generate_data.py         # Orchestrator: run all builders
│   └── builders/                # One builder per category (01-14)
├── databases/                   # Generated SQLite files (gitignored)
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── database.py              # Multi-DB connection + progress.db management
│   ├── models/schemas.py        # Pydantic request/response models
│   └── routers/
│       ├── categories.py        # GET /api/categories
│       ├── problems.py          # GET /api/problems, /api/problems/{id}, /tables
│       ├── progress.py          # POST/PATCH /api/progress/{id}, /summary
│       └── databases.py         # GET /api/databases/{id}/connect
└── frontend/
    └── src/
        ├── types.ts             # TypeScript interfaces
        ├── api.ts               # API client functions
        ├── App.tsx              # Router setup
        └── pages/
            ├── CategoryListPage.tsx
            └── ProblemListPage.tsx
```

## 🔧 Customization

### Adding a new problem

1. Add a `Problem` entry in `data_builder/manifest.py`
2. Create a builder function in the corresponding category file under `data_builder/builders/`
3. Run `python3 data_builder/generate_data.py`

### Adding a new category

1. Add a `Category` entry in `data_builder/manifest.py`
2. Create a new builder file `data_builder/builders/XX_topic_name.py` with a `build(conn)` function
3. Run `python3 data_builder/generate_data.py`

## 📄 License

MIT

---

> 📖 [中文文档](README_zh.md)

## 🙏 Acknowledgments

Problem content adapted from 语兴's "踏踏实实练SQL" series ([Bilibili](https://space.bilibili.com/405479587) | [WeChat: 语数](https://ydata.vip)). Used for educational purposes.
