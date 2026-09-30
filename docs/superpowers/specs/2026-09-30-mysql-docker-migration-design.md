# SQL 练习环境迁移 MySQL 8（Docker） 设计文档

日期：2026-09-30
状态：已获用户批准

## 1. 背景与问题

用户在 DBeaver 中对本地 SQLite 练习库写 SQL 时遇到 `no such function` 报错。排查确认：

- 本机 SQLite 并不缺窗口函数：命令行 sqlite3 为 3.51.0，Python sqlite3 为 3.53.2，均远高于窗口函数引入版本 3.25（2018）
- 真正报错的是 **Hive 方言函数**（`DATEDIFF`、`DATE_ADD(..., INTERVAL)`、`collect_list`、`explode` 等）——SQLite 无论怎么升级都不会有这些函数
- 根因是**练习引擎与题目口径不匹配**：`docs/sql-interview-review.md` 手册口径为 Hive SQL，`data_builder/manifest.py` 部分参考答案也是 Hive 写法，而练习库是 SQLite

用户目标面试口径为 **MySQL 为主**（后端/通用研发岗）。MySQL 8 原生支持窗口函数全家桶、`DATEDIFF`、`DATE_ADD(..., INTERVAL)`、`GROUP_CONCAT`、`JSON_TABLE`，与面试口径完全一致。

## 2. 方案选型记录

| 方案 | 结论 | 理由 |
|---|---|---|
| **A. Docker 跑官方 mysql:8 镜像** | **采用** | 真 MySQL 8，与面试口径 100% 一致；环境隔离可重复；3306 端口空闲，Docker 27.5.1 已就绪 |
| B. 启动本地 MariaDB 12 | 否决 | 本机已有 MariaDB 12.0.2（brew，服务未启动）但 MariaDB ≠ MySQL 8：无 `JSON_TABLE`、JSON 函数体系有差异，等于换一套新的方言微差 |
| C. 升级 SQLite + 答案改 SQLite 方言 | 否决 | SQLite 版本已够新；`julianday`/`date(x,'+1 day')` 不是面试考的口径 |

改造范围（用户选定）：**全部对齐 MySQL**——练习库、manifest 参考答案、复习手册口径标注一起迁移。

## 3. 需求决策记录

| 决策点 | 结论 |
|---|---|
| 练习引擎 | Docker 单容器 mysql:8.4（当前 LTS），每专题一个 schema（专题 12 无表，实际生成 13 个） |
| 面试口径 | MySQL 8 为主轴；Hive 专属函数处保留一行对照标注 |
| 进度存储 | `progress.db` 保持 SQLite 不迁移（进度数据需保留，练习数据可再生） |
| sql_mode | 保持默认严格模式（含 `ONLY_FULL_GROUP_BY`），与真实面试环境一致 |
| 凭据 | `root / practice`，端口绑定 `127.0.0.1:3306` 仅本机访问 |
| stub 题目 | 专题 12 的 5 题与 14 的 2 题保持 stub，补题不在本次范围 |
| 遗留未提交 diff | `databases.py`/`problems.py` 中连接串改纯路径的两处修改将被 MySQL 连接信息取代 |

## 4. 总体架构与数据流

```
┌──────────┐  JDBC        ┌─────────────────────────┐
│  DBeaver │─────────────▶│ mysql:8 容器             │
└──────────┘              │ 127.0.0.1:3306 (仅本机) │
                          │ 13 个 schema（专题 12 无表跳过）│
┌──────────┐  HTTP        └───────────▲─────────────┘
│ React 前端│◀════════▶ FastAPI 后端   │ SQLAlchemy + PyMySQL
└──────────┘    │                     │
                ▼                     │
        progress.db（SQLite，保持不动）
                ▲
        data_builder（仅重写连接层）
```

### 4.1 组件与改动

| 组件 | 改动 | 职责 |
|---|---|---|
| `docker-compose.yml` | 新增 | mysql:8 单容器、健康检查、named volume `mysql_data` |
| `data_builder/db.py` | 新增 | `connect(schema)` 返回 PyMySQL DBAPI 连接，builder 改动最小化 |
| `data_builder/generate_data.py` | 改造 | 每专题 `DROP DATABASE IF EXISTS` + `CREATE DATABASE ... utf8mb4` 后调 builder |
| `data_builder/builders/*.py` | 方言适配 | 建表/插数 SQL 按 §5 适配表改写，逻辑不动 |
| `data_builder/manifest.py` | 口径改写 | 44 题 `reference_sql` 逐题改为 MySQL 8 可执行写法 |
| `backend/routers/databases.py` | 小改 | connect 端点返回 MySQL 连接信息（JDBC URL + mysql CLI 命令） |
| `backend/routers/problems.py` | 小改 | `db_connection` 字段改 MySQL 口径；`/tables` 端点改读 MySQL |
| `backend/database.py` | 小改 | `get_table_schema()` 从 `PRAGMA table_info` 改查 `information_schema` |
| `backend/routers/progress.py`、`categories.py` | 不动 | progress.db 继续 SQLite |
| `frontend/ProblemListPage.tsx` | 微调 | 复制内容改为 MySQL 连接方式 |
| `docs/sql-interview-review.md` | 口径更新 | 差异标注从"SQLite 差异"改为"MySQL 8 主轴 + Hive 对照" |
| `README.md` / `README_zh.md` | 更新 | 环境说明改为 MySQL 8 (Docker)，新增 Docker 前置要求 |
| `start.sh` | 改造 | 集成容器启动与健康等待（§6） |
| `data_builder/smoke_test.py` | 新增 | 冒烟验证：遍历非 stub 题目逐题执行 `reference_sql`（§7） |

### 4.2 数据流

- **重置流**：`start.sh` → `docker compose up -d` → 等容器 healthy → `generate_data.py` 清空重建各专题 schema → 题目元数据 seed 进 progress.db
- **练习流**：浏览器看题/记进度（不依赖容器）；DBeaver 连 `127.0.0.1:3306` 写 SQL（依赖容器）

## 5. 方言适配约定

### 5.1 建表与插数（SQLite → MySQL 8）

| SQLite 写法 | MySQL 8 写法 |
|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `INT AUTO_INCREMENT PRIMARY KEY` |
| `TEXT` 主键 / 无类型列 | `VARCHAR(n)`（补明确长度） |
| 标识符 | 统一反引号包裹（schema 名以数字开头，如 `01_continuous_login`） |
| `?` 占位符 | `%s` |
| `datetime('now')` | `NOW()` |
| `julianday()` 差值 | `DATEDIFF()` |
| `conn.execute` / `conn.executemany` | `cur = conn.cursor()` 后在 cursor 上调用同名 API（PyMySQL 连接无便捷方法） |

### 5.2 参考答案（Hive → MySQL 8）

| Hive/SQLite 写法 | MySQL 8 写法 | 备注 |
|---|---|---|
| `DATEDIFF(end, start)` | 同名同序（expr1 − expr2） | 直接可用 |
| `DATE_ADD(x, INTERVAL n DAY)` | 原生支持 | 直接可用 |
| `collect_list(col)` | `GROUP_CONCAT` / `JSON_ARRAYAGG` | 需保留结构时用后者 |
| `explode` / `LATERAL VIEW` | `JSON_TABLE()` | MySQL 8 面试高频考点 |
| `nvl()` | `IFNULL()` | |
| `date(x,'+1 day')`（SQLite） | `DATE_ADD(x, INTERVAL 1 DAY)` | |

改写原则：**语义不变，只换方言表达**；逐题在生成的真实数据上跑通为准，不做纸面改写。

## 6. 错误处理

1. Docker daemon 未运行 → `start.sh` 明确提示"请先启动 Docker Desktop"
2. 3306 端口被占用 → 提示停掉占用进程或修改 compose 端口映射
3. 容器 healthy 等待超时（60 秒）→ 报错退出，不挂死
4. `generate_data.py` 连不上 MySQL → 重试一次后报错并提示查看容器状态
5. 参考答案在 `ONLY_FULL_GROUP_BY` 下报错 → **视为答案 bug 改写答案**，不放宽 sql_mode
6. 前端复制内容提供两种格式：DBeaver JDBC URL（如 `jdbc:mysql://127.0.0.1:3306/01_continuous_login`，用户名 `root`、密码 `practice`）+ `mysql` CLI 一行命令（如 `mysql -h 127.0.0.1 -P 3306 -uroot -ppractice 01_continuous_login`）

## 7. 验收标准

- [ ] `docker compose up` + 数据生成全绿，13 个 schema 就绪（专题 12 无表，跳过）
- [ ] 冒烟脚本：遍历全部非 stub 题目，逐题在对应 schema 执行 `reference_sql`，严格模式下 0 报错——口径对齐的硬验收
- [ ] `bash start.sh` 冷启动一键跑通
- [ ] 前端看题 / 表结构 / 样例数据 / 进度功能回归正常
- [ ] 手册无残留误导性 SQLite 口径标注

## 8. 范围外

- 专题 12 的 5 道 stub 题与 14 的 2 道 stub 题的补题（内容工作，另行处理）
- progress.db 迁移 MySQL（无必要）
- 多用户/权限体系（本地单人练习）
