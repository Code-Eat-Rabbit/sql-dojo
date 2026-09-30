# SQL 练习环境迁移 MySQL 8（Docker） 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 把 SQL Dojo 的练习库从本地 SQLite 文件迁移到 Docker 单容器 MySQL 8（13 个 schema），manifest 参考答案与复习手册口径全部对齐 MySQL 8，前端/后端/start.sh 配套改造。

**架构：** `docker-compose.yml` 跑 mysql:8.4（127.0.0.1:3306，root/practice），`data_builder` 经 PyMySQL 每专题重建一个 schema；`progress.db` 保持 SQLite 只存进度；DBeaver 直连 MySQL 练习，浏览器看题记进度。规格：`docs/superpowers/specs/2026-09-30-mysql-docker-migration-design.md`。

**技术栈：** Docker Compose、mysql:8.4、PyMySQL + cryptography、FastAPI（不变）、React/Vite（微调）。

**重要背景（执行前必读）：**

- 项目无任何测试基建（无 pytest、无 tests/）。本计划的"测试"= `data_builder/smoke_test.py` 冒烟脚本 + 逐步运行验证命令。
- `backend/routers/databases.py` 与 `backend/routers/problems.py` 当前有**未提交的工作区改动**（连接串从 `sqlite:///` 改为裸路径）。这些改动会被本计划取代，属预期。
- 所有命令都在项目根 `/Users/yourton_ma/Documents/sql_practice` 下执行。
- schema 命名 = `cat.db_file` 去掉 `.db` 后缀（如 `01_continuous_login`）。专题 12 无表不生成 schema。
- MySQL 8 字符集默认 utf8mb4；连接层统一 `charset="utf8mb4"`。
- 日期/时间字符串列统一 `VARCHAR(20)`（容纳 `YYYY-MM-DD HH:MM:SS`），月份 `VARCHAR(7)`，纯日期 `VARCHAR(10)`，名称类 `VARCHAR(128)`，ID 类 `VARCHAR(64)`，长内容 `VARCHAR(512)` 或 `TEXT`，`REAL` → `DOUBLE`。

---

### 任务 1：Docker Compose 起 MySQL 8 容器

**文件：**
- 创建：`docker-compose.yml`

- [ ] **步骤 1：编写 docker-compose.yml**

```yaml
name: sql-dojo-mysql

services:
  mysql:
    image: mysql:8.4
    container_name: sql-dojo-mysql
    restart: unless-stopped
    ports:
      - "127.0.0.1:3306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: practice
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-uroot", "-ppractice"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  mysql_data:
```

- [ ] **步骤 2：启动容器（首次拉镜像约 200MB）**

运行：`docker compose up -d && docker compose ps`
预期：STATUS 为 `Up (healthy)`（首次初始化约需 20-30 秒才变 healthy，可重复执行 `docker compose ps` 观察）

- [ ] **步骤 3：验证连通与版本**

运行：`docker compose exec -T mysql mysql -uroot -ppractice -e "SELECT VERSION(); SHOW DATABASES;"`
预期：VERSION 为 `8.4.x`；数据库列表只有 information_schema / mysql / performance_schema / sys

- [ ] **步骤 4：Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add mysql:8.4 docker compose for practice engine"
```

---

### 任务 2：添加 Python 依赖

**文件：**
- 修改：`pyproject.toml`、`uv.lock`（由 uv 自动维护）

- [ ] **步骤 1：添加 PyMySQL 与 cryptography**

运行：`uv add pymysql cryptography`
说明：PyMySQL 连 MySQL 8 默认认证插件 `caching_sha2_password` 时必须依赖 `cryptography`。

- [ ] **步骤 2：验证安装**

运行：`uv run python -c "import pymysql, cryptography; print(pymysql.__version__)"`
预期：输出版本号（如 `1.1.x`），无 ImportError

- [ ] **步骤 3：Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add pymysql and cryptography dependencies"
```

---

### 任务 3：data_builder 连接层 db.py

**文件：**
- 创建：`data_builder/db.py`

- [ ] **步骤 1：编写 db.py（完整文件）**

```python
"""MySQL 连接层：练习库 schema 管理（替代原 SQLite 单文件模式）"""

import time

import pymysql

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "practice"


def connect(schema: str | None = None) -> pymysql.connections.Connection:
    """返回 utf8mb4、autocommit 的 PyMySQL 连接，可选直连某个 schema"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=schema,
        charset="utf8mb4",
        autocommit=True,
    )


def reset_schema(schema: str) -> pymysql.connections.Connection:
    """DROP + CREATE 指定 schema，返回已选中该 schema 的连接"""
    conn = connect()
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{schema}`")
        cur.execute(f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4")
    conn.select_db(schema)
    return conn


def wait_for_mysql(timeout: int = 60) -> None:
    """轮询等待 MySQL 可连接，超时抛 SystemExit"""
    deadline = time.time() + timeout
    last_err = None
    while time.time() < deadline:
        try:
            connect().close()
            return
        except pymysql.err.OperationalError as e:
            last_err = e
            time.sleep(1)
    raise SystemExit(f"MySQL 在 {timeout}s 内不可达（127.0.0.1:3306）: {last_err}")


if __name__ == "__main__":
    wait_for_mysql()
    conn = connect()
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        print("MySQL OK, version:", cur.fetchone()[0])
    conn.close()
```

- [ ] **步骤 2：运行自检**

运行：`uv run python data_builder/db.py`
预期：输出 `MySQL OK, version: 8.4.x`

- [ ] **步骤 3：Commit**

```bash
git add data_builder/db.py
git commit -m "feat: add MySQL connection layer for data_builder"
```

---

### 任务 4：generate_data.py 改造

**文件：**
- 修改：`data_builder/generate_data.py`（现 75 行）

保持不变的部分：`builders_to_run` 的计算与跳过逻辑（L28-37）、builder 的动态导入（L39-51）、L65-68 的 progress.db 段（`init_progress_db` + `seed_problems`，继续走 SQLite）。

- [ ] **步骤 1：修改 import 区（文件头部）**

删除 `import sqlite3`（若存在），新增：

```python
import time

from data_builder import db as mysql_db
```

注意：`sys.path` 注入在 import sqlite3 之后的话，`from data_builder import db` 需放在 sys.path 注入之后（现有 L12-13 已注入，紧随其后即可）。

- [ ] **步骤 2：替换 ensure_db 函数（原 L16-22）**

```python
def ensure_db(category) -> pymysql.connections.Connection:
    """每个 category 一个 MySQL schema：DROP 后重建，替代原删 .db 文件逻辑"""
    schema = category.db_file[:-3]  # "01_continuous_login.db" -> "01_continuous_login"
    return mysql_db.reset_schema(schema)
```

文件顶部补 `import pymysql`（用于类型标注），或省略返回类型标注直接写 `def ensure_db(category):`。

- [ ] **步骤 3：替换表清单查询（原 L56-58 的 sqlite_master）**

```python
            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = DATABASE() ORDER BY table_name"
            ).fetchall()
            table_names = [t[0] for t in tables]
```

后续 `SELECT COUNT(*) FROM {tname}` 循环改用 `table_names` 中的值，表名用反引号包裹：

```python
            for tname in table_names:
                cnt = conn.execute(f"SELECT COUNT(*) FROM `{tname}`").fetchone()[0]
```

（保持原有打印格式，仅数据来源更换。）

- [ ] **步骤 4：修改 run_all 与入口，加入等待与重试**

`run_all()` 开头（builders 循环之前）不需要改动等待逻辑；在文件末尾入口改为：

```python
if __name__ == "__main__":
    try:
        mysql_db.wait_for_mysql(timeout=30)
    except SystemExit:
        print("⚠️  MySQL 首次连接失败，5 秒后重试一次...")
        time.sleep(5)
        try:
            mysql_db.wait_for_mysql(timeout=30)
        except SystemExit as e:
            raise SystemExit(f"{e}\n请检查容器状态：docker compose ps && docker compose logs mysql")
    run_all()
```

`conn.commit()`（原 L53）可保留（autocommit 下无操作，无害），也可删除。

- [ ] **步骤 5：运行验证（此时 builders 仍是 SQLite 写法，预期报错）**

运行：`uv run python data_builder/generate_data.py`
预期：能连上 MySQL、`01_continuous_login` schema 被创建，随后在 builder 内报错（`?` 占位符或 `sqlite3.Connection` 相关）——**这是预期失败**，builders 在任务 5-7 修复。若报错发生在 MySQL 连接/schema 创建阶段则本任务有问题。

- [ ] **步骤 6：Commit**

```bash
git add data_builder/generate_data.py
git commit -m "feat: generate_data orchestrates MySQL schemas instead of sqlite files"
```

---

### 任务 5：builders 01–04 方言适配

**文件：**
- 修改：`data_builder/builders/01_continuous_login.py`、`02_window_lead_lag.py`、`03_window_rank.py`、`04_cumulative_agg.py`

**通用改法（每个文件都做，下同）：**

1. 删除 `import sqlite3`；`def build(conn: sqlite3.Connection):` → `def build(conn):`
2. `?` 占位符 → `%s`：先 `grep -n '?' <文件>` 确认所有 `?` 都在 SQL 字符串内，再执行 `sed -i '' 's/?/%s/g' <文件>`，之后 `grep -n '?' <文件>` 应零命中
3. DDL 中 `TEXT` 列按下方映射改 `VARCHAR(n)`；`REAL` → `DOUBLE`；`INTEGER` 保留
4. DDL/INSERT 中的表名与列名不用加反引号（本组无保留字）

**列类型映射表（SQLite TEXT → MySQL VARCHAR）：**

| 文件 | 表.列 | 新类型 |
|---|---|---|
| 01 | test.date、account.date | VARCHAR(20) |
| 01 | test_xiaoming.name | VARCHAR(128) |
| 01 | test_xiaoming.start_date / end_date | VARCHAR(10) |
| 01 | games.date | VARCHAR(20)；games.result → VARCHAR(128) |
| 02 | stock_price.ds、data_table.date、metrics.date | VARCHAR(20) |
| 03 | scores.student、student_scores.student、student_scores.subject | VARCHAR(128) |
| 04 | user_visits.month_id | VARCHAR(7) |
| 04 | live_log.login_time / logout_time | VARCHAR(20) |
| 04 | user_spend.dt | VARCHAR(10) |
| 04 | orders.product_id / order_id | VARCHAR(64) |
| 04 | product_price.ds | VARCHAR(10)；product_price.id 若为 TEXT → VARCHAR(64) |

- [ ] **步骤 1：按通用改法 + 映射表修改 4 个文件**
- [ ] **步骤 2：残留检查**

运行：`grep -rn 'sqlite3\|TEXT' data_builder/builders/01_continuous_login.py data_builder/builders/02_window_lead_lag.py data_builder/builders/03_window_rank.py data_builder/builders/04_cumulative_agg.py`
预期：零命中

- [ ] **步骤 3：运行数据生成**

运行：`uv run python data_builder/generate_data.py`
预期：此时 01-04 打印表与行数成功；05 及之后仍报错（后续任务修复）

- [ ] **步骤 4：验证 schema 内容**

运行：`docker compose exec -T mysql mysql -uroot -ppractice -e "SHOW TABLES IN 01_continuous_login; SELECT COUNT(*) FROM 01_continuous_login.test; SHOW CREATE TABLE 01_continuous_login.games\G" | head -30`
预期：4 张表（test/account/test_xiaoming/games），行数与生成日志一致，games 列类型为 varchar

- [ ] **步骤 5：Commit**

```bash
git add data_builder/builders/01_continuous_login.py data_builder/builders/02_window_lead_lag.py data_builder/builders/03_window_rank.py data_builder/builders/04_cumulative_agg.py
git commit -m "refactor: migrate builders 01-04 to MySQL dialect"
```

---

### 任务 6：builders 05–09 方言适配（含 05 保留字修复）

**文件：**
- 修改：`data_builder/builders/05_explode.py`、`06_joins.py`、`07_retention.py`、`08_expand_contract.py`、`09_merge_interval.py`

**通用改法：** 同任务 5（删 sqlite3 import、`?`→`%s`、类型映射）。

**列类型映射表：**

| 文件 | 表.列 | 新类型 |
|---|---|---|
| 05 | raw_intervals."end" | INTEGER 保留（只改引号，见下） |
| 06 | student.student_name、class.class_name | VARCHAR(128) |
| 06 | fans.from_user / to_user | VARCHAR(128) |
| 06 | student.id / class.id | `INTEGER PRIMARY KEY` 保留（MySQL 直接支持；builder 显式插入 id，无 AUTOINCREMENT） |
| 07 | user_active.date | VARCHAR(20) |
| 08 | user_tags.tags | VARCHAR(512) |
| 08 | user_tag_rows.tag | VARCHAR(128) |
| 09 | status_log.status | VARCHAR(128) |
| 09 | status_log.start_time | VARCHAR(20) |
| 09 | data_table.date | VARCHAR(10)（该表含 NULL 值，PyMySQL 原生支持） |

**05_explode.py 专属修复（保留字 `end`，双引号在 MySQL 中是字符串）：**

- L12 DDL：`"end" INTEGER` → `` `end` INTEGER ``
- L36 INSERT：`INSERT INTO raw_intervals (start, "end") VALUES (%s, %s)`（改占位符后）→ `` INSERT INTO raw_intervals (start, `end`) VALUES (%s, %s) ``

- [ ] **步骤 1：按通用改法 + 映射表 + 05 专属修复修改 5 个文件**
- [ ] **步骤 2：残留检查**

运行：`grep -rn 'sqlite3\|TEXT\|"end"' data_builder/builders/0[5-9]*.py`
预期：零命中

- [ ] **步骤 3：运行数据生成**

运行：`uv run python data_builder/generate_data.py`
预期：01-09 全部成功，10 及之后仍报错

- [ ] **步骤 4：验证 05 schema（保留字表已可建）**

运行：`docker compose exec -T mysql mysql -uroot -ppractice -e "SHOW CREATE TABLE 05_explode.raw_intervals\G" | head -15`
预期：列 `` `end` `` int 存在

- [ ] **步骤 5：Commit**

```bash
git add data_builder/builders/05_explode.py data_builder/builders/06_joins.py data_builder/builders/07_retention.py data_builder/builders/08_expand_contract.py data_builder/builders/09_merge_interval.py
git commit -m "refactor: migrate builders 05-09 to MySQL dialect (fix reserved word 'end')"
```

---

### 任务 7：builders 10、11、13、14 方言适配（含 13 保留字、14 加 idx 列）

**文件：**
- 修改：`data_builder/builders/10_hr_warehouse.py`、`11_date_processing.py`、`13_json_parsing.py`、`14_fun_sql.py`
- 不动：`data_builder/builders/12_company_questions.py`（stub，build() 永不执行；顺手删除其未使用的 `import sqlite3` 亦可，非必须）

**列类型映射表：**

| 文件 | 表.列 | 新类型 |
|---|---|---|
| 10 | employee.name / status | VARCHAR(128) |
| 10 | employee.hire_date | VARCHAR(10) |
| 10 | salary.month | VARCHAR(7)；复合主键 `PRIMARY KEY (emp_id, month)` 保留 |
| 10 | attendance.date | VARCHAR(10)；check_in / check_out → VARCHAR(20) |
| 11 | date_table.date | VARCHAR(10)（题目依赖 SUBSTR，保持字符串） |
| 13 | json_table.data | TEXT（合法 JSON 字符串，保持 TEXT） |
| 14 | race_result.horse | VARCHAR(128)；time REAL → DOUBLE |
| 14 | heights | 见下方专属改造 |

**13_json_parsing.py 专属修复（表名撞 MySQL 8 保留函数 `JSON_TABLE`）：**

- DDL L11：`CREATE TABLE IF NOT EXISTS json_table (` → `` CREATE TABLE IF NOT EXISTS `json_table` (``
- INSERT L32：`INSERT INTO json_table (id, data) VALUES (%s, %s)` → `` INSERT INTO `json_table` (id, data) VALUES (%s, %s) ``

**14_fun_sql.py 专属改造（接雨水需要确定的柱子顺序，`ROW_NUMBER() OVER ()` 在 MySQL 中顺序不确定）：**

heights 表加 `idx` 列。DDL 改为：

```python
    conn.execute("""
        CREATE TABLE IF NOT EXISTS heights (
            idx INTEGER,
            height INTEGER
        )
    """)
```

插入数据改为：

```python
    heights_data = [(i + 1, h) for i, h in enumerate(heights_vals)]
    conn.executemany("INSERT INTO heights (idx, height) VALUES (%s, %s)", heights_data)
```

- [ ] **步骤 1：按通用改法 + 映射表 + 13/14 专属修复修改 4 个文件**
- [ ] **步骤 2：残留检查**

运行：`grep -rn 'sqlite3\|TEXT\| REAL' data_builder/builders/1*.py`
预期：仅 13 的 `data TEXT` 一处命中（有意保留），其余零命中

- [ ] **步骤 3：运行数据生成（应首次全绿）**

运行：`uv run python data_builder/generate_data.py`
预期：13 个 schema 全部生成（12 跳过），每表打印行数，末尾 progress.db 初始化成功

- [ ] **步骤 4：验证全部 schema**

运行：`docker compose exec -T mysql mysql -uroot -ppractice -N -e "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE '0%' OR schema_name LIKE '1%' ORDER BY schema_name"`
预期：恰好 13 行，`01_continuous_login` … `14_fun_sql`（无 12）

- [ ] **步骤 5：Commit**

```bash
git add data_builder/builders/10_hr_warehouse.py data_builder/builders/11_date_processing.py data_builder/builders/13_json_parsing.py data_builder/builders/14_fun_sql.py
git commit -m "refactor: migrate builders 10-14 to MySQL dialect (json_table backticks, heights idx)"
```

---

### 任务 8：冒烟脚本 smoke_test.py（TDD 红灯）

**文件：**
- 创建：`data_builder/smoke_test.py`

冒烟脚本是本迁移的**唯一自动化测试**：逐题在真实 schema 上执行 `reference_sql`，并做方言 lint（抓"能跑但语义错"的写法，如 MySQL 中 `||` 是逻辑 OR、`GROUP_CONCAT(x, ',')` 双参分隔符语法）。

- [ ] **步骤 1：编写 smoke_test.py（完整文件）**

```python
"""参考答案冒烟测试：逐题在 MySQL 上执行 reference_sql。

用法：uv run python data_builder/smoke_test.py
分类：
  executable   逐语句执行，必须 0 报错
  ddl          答案全为 CREATE TABLE，在 smoke_scratch 库执行后清理
  comment_only 纯注释说明题，跳过
  stub         -- 待补充，跳过
另外对 executable 答案做方言 lint（|| / JSON_EACH / mydb. 等禁止模式）。
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_builder import db as mysql_db
from data_builder.manifest import CATEGORIES, get_all_problems

SCHEMAS = {cat.id: cat.db_file[:-3] for cat in CATEGORIES}

FORBIDDEN_PATTERNS = [
    (r"\|\|", "SQLite 拼接 || → 用 CONCAT()"),
    (r"JSON_EACH", "SQLite JSON_EACH → 用 JSON_TABLE()"),
    (r"julianday|strftime|sqlite_master|AUTOINCREMENT", "SQLite 专属语法"),
    (r"\bmydb\.", "跨库前缀 mydb. → 去掉，题内表就在当前 schema"),
    (r"GROUP_CONCAT\([^)]*,\s*'", "GROUP_CONCAT 双参分隔符 → 用 SEPARATOR"),
]


def strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        cut = line.find("--")
        lines.append(line if cut == -1 else line[:cut])
    return "\n".join(lines)


def statements(sql: str) -> list[str]:
    return [s.strip() for s in strip_comments(sql).split(";") if s.strip()]


def classify(sql: str) -> str:
    if "待补充" in sql:
        return "stub"
    stmts = statements(sql)
    if not stmts:
        return "comment_only"
    if all(s.lstrip().upper().startswith("CREATE") for s in stmts):
        return "ddl"
    return "executable"


def lint(sql: str) -> list[str]:
    return [msg for pat, msg in FORBIDDEN_PATTERNS if re.search(pat, sql, re.IGNORECASE)]


def run_problem(prob) -> tuple[str, str]:
    kind = classify(prob.reference_sql)
    if kind in ("stub", "comment_only"):
        return kind, "skip"
    target = mysql_db.reset_schema("smoke_scratch") if kind == "ddl" \
        else mysql_db.connect(SCHEMAS[prob.category_id])
    try:
        issues = lint(prob.reference_sql)
        if issues:
            return kind, "lint: " + "; ".join(issues)
        for stmt in statements(prob.reference_sql):
            with target.cursor() as cur:
                cur.execute(stmt)
                if cur.description:
                    cur.fetchall()
        return kind, "ok"
    finally:
        target.close()


def main() -> int:
    mysql_db.wait_for_mysql()
    failures = []
    counts = {"executable": 0, "ddl": 0, "comment_only": 0, "stub": 0}
    for prob in get_all_problems():
        try:
            kind, status = run_problem(prob)
        except Exception as e:  # pymysql 报错等
            kind = classify(prob.reference_sql)
            status = f"FAIL: {str(e)[:160]}"
        counts[kind] = counts.get(kind, 0) + 1
        mark = "✓" if status == "ok" or status == "skip" else "✗"
        print(f"[{mark}] {prob.id:<6} {kind:<12} {status}")
        if mark == "✗":
            failures.append(prob.id)
    # 清理 scratch 库
    conn = mysql_db.connect()
    with conn.cursor() as cur:
        cur.execute("DROP DATABASE IF EXISTS smoke_scratch")
    conn.close()
    print(f"\n统计: {counts}")
    print("失败:", failures if failures else "无")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **步骤 2：首次运行，确认红灯（预期失败清单）**

运行：`uv run python data_builder/smoke_test.py; echo "exit=$?"`
预期 `exit=1`，失败清单**恰好 13 题**：
`['01_01', '01_02', '01_05', '01_06', '04_02', '04_03', '04_04', '04_08', '08_01', '08_02', '11_02', '13_01', '14_01']`
逐题预期原因：01_01/01_05 Hive `date_add`/`date_sub` 两参语法错；01_02 `FROM (第三步子查询)` 语法错；01_06 lint `mydb.`；04_02/03/04 `FROM (步骤一)` 语法错；04_08 窗口函数在 WHERE（MySQL 错误 3593）；08_01 lint `||`；08_02 lint GROUP_CONCAT 双参；11_02 lint `||`；13_01 lint `JSON_EACH`；14_01 `invalid use of group function`。
说明：10_02（SQLite 风格 DDL）在 scratch 库中语法可执行，首跑即为 ✓，任务 9 对它的改写只是类型规范化，不改变红绿状态。
若失败清单之外的题也失败，先排查 builders 数据问题再进入任务 9。

- [ ] **步骤 3：Commit（红灯也是成果）**

```bash
git add data_builder/smoke_test.py
git commit -m "test: add reference_sql smoke test (currently 13-14 expected failures)"
```

---

### 任务 9：manifest 参考答案改写——方言 10 题

**文件：**
- 修改：`data_builder/manifest.py`（下列题目的 `reference_sql` 字段，行号为现文件行号，改写后行数会漂移）

改写原则：语义不变，只换方言表达。以下每题给出完整替换文本。

- [ ] **步骤 1：01_01（行 84-100，Hive date_add 两参 + 伪占位）替换为**

```sql
-- 步骤一：去重
SELECT id, SUBSTR(date, 1, 10) AS date
FROM test
GROUP BY id, SUBSTR(date, 1, 10);

-- 步骤二：用 row_number 标记分组（日期减去行号，连续日期得到相同 date1）
WITH numbered AS (
    SELECT id, date,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY date) AS rn
    FROM (
        SELECT id, SUBSTR(date, 1, 10) AS date
        FROM test
        GROUP BY id, SUBSTR(date, 1, 10)
    ) dedup
)
SELECT id, date,
       DATE_ADD(date, INTERVAL -rn DAY) AS date1
FROM numbered;

-- 步骤三：统计连续天数
WITH numbered AS (
    SELECT id, date,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY date) AS rn
    FROM (
        SELECT id, SUBSTR(date, 1, 10) AS date
        FROM test
        GROUP BY id, SUBSTR(date, 1, 10)
    ) dedup
),
flagged AS (
    SELECT id, DATE_ADD(date, INTERVAL -rn DAY) AS date1
    FROM numbered
)
SELECT id, date1, COUNT(*) AS day_cnt
FROM flagged
GROUP BY id, date1
HAVING COUNT(*) > 3;
```

- [ ] **步骤 2：01_05（行 212-225，Hive date_sub 两参）替换为**

```sql
-- 先筛选余额 > 1000 的行，再套用连续类题的思路
WITH filtered AS (
    SELECT user_id, date, balance
    FROM account
    WHERE balance > 1000
),
numbered AS (
    SELECT user_id, date,
           ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date) AS rn
    FROM filtered
),
flagged AS (
    SELECT user_id,
           DATE_SUB(date, INTERVAL rn DAY) AS grp
    FROM numbered
)
SELECT user_id, grp, COUNT(*) AS consecutive_days
FROM flagged
GROUP BY user_id, grp
HAVING COUNT(*) > 1;
```

- [ ] **步骤 3：04_08（行 681-691，窗口函数误放 WHERE）替换为**

```sql
WITH min_so_far AS (
    SELECT id, ds, price,
           MIN(price) OVER (PARTITION BY id ORDER BY ds) AS min_price_so_far,
           LAG(price) OVER (PARTITION BY id ORDER BY ds) AS prev_price
    FROM product_price
)
SELECT id, ds, price
FROM min_so_far
WHERE price = min_price_so_far
  AND price < prev_price;
```

- [ ] **步骤 4：08_01（行 886-899，`||` 拼接 + 递归 CTE 列宽）替换为**

```sql
-- MySQL 8 用递归 CTE 模拟 explode（对应 Hive 的 lateral view explode）
-- CAST 锚定列宽，避免递归部分 SUBSTR 结果被截断
WITH RECURSIVE split(user_id, tag, rest) AS (
    SELECT user_id, CAST('' AS CHAR(128)), CONCAT(tags, ',')
    FROM user_tags
    UNION ALL
    SELECT user_id,
           SUBSTR(rest, 1, INSTR(rest, ',') - 1),
           SUBSTR(rest, INSTR(rest, ',') + 1)
    FROM split
    WHERE rest != ''
)
SELECT user_id, tag FROM split WHERE tag != '';
```

- [ ] **步骤 5：08_02（行 917-922，GROUP_CONCAT 分隔符语法）替换为**

```sql
SELECT user_id,
       GROUP_CONCAT(tag SEPARATOR ',') AS tags
FROM user_tag_rows
GROUP BY user_id;
```

- [ ] **步骤 6：11_02（行 1084-1088，`||` + CAST AS TEXT + 整数除法）替换为**

```sql
SELECT date,
       CONCAT(SUBSTR(date, 1, 4), 'Q',
              (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 3 + 1) AS quarter
FROM date_table;
```

- [ ] **步骤 7：13_01（行 1197-1208，JSON_EACH + 保留字表名）替换为**

```sql
-- MySQL 8 内置 JSON 函数
SELECT id,
       JSON_EXTRACT(data, '$.name') AS name,
       JSON_EXTRACT(data, '$.age') AS age
FROM `json_table`;

-- 展开 JSON 数组（JSON_TABLE 是 MySQL 8 表函数，对应 Hive 的 lateral view explode）
SELECT jt.id,
       items.item
FROM `json_table` jt,
     JSON_TABLE(jt.data, '$.items[*]'
         COLUMNS (item VARCHAR(64) PATH '$')) AS items;
```

同题 `description`（行 1192-1196）替换为：

```text
MySQL 8 中解析 JSON 字段的方法（JSON_EXTRACT 提取字段，JSON_TABLE 展开数组）。

English: Parse JSON fields in MySQL 8: JSON_EXTRACT() to access keys, JSON_TABLE() to expand arrays (the MySQL counterpart of Hive's explode).
```

同题 `hints`（行 1210-1213）替换为：

```python
                hints=[
                    "JSON_EXTRACT(col, '$.key') 提取字段",
                    "JSON_TABLE(col, '$.array[*]' COLUMNS (...)) 展开数组"
                ],
```

- [ ] **步骤 8：14_01（行 1234-1252，SQLite 标量 MIN(a,b) + 聚合嵌套）替换为**

```sql
WITH left_max AS (
    SELECT idx, height,
           MAX(height) OVER (ORDER BY idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS lmax
    FROM heights
),
right_max AS (
    SELECT idx, height, lmax,
           MAX(height) OVER (ORDER BY idx DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS rmax
    FROM left_max
)
SELECT SUM(LEAST(lmax, rmax) - height) AS total_water
FROM right_max
WHERE LEAST(lmax, rmax) > height;
```

（heights 表已在任务 7 加了 idx 列。）

- [ ] **步骤 9：01_06（行 243-264）单行修复**

`FROM mydb.test_xiaoming` → `FROM test_xiaoming`（其余不动）。

- [ ] **步骤 10：10_02（行 1017-1043，SQLite 风格 DDL）替换为**

```sql
-- 员工表
CREATE TABLE employee (
    emp_id INT PRIMARY KEY,
    name VARCHAR(128),
    dept_id INT,
    hire_date VARCHAR(10),
    status VARCHAR(128)
);

-- 薪资表
CREATE TABLE salary (
    emp_id INT,
    month VARCHAR(7),
    base_salary DOUBLE,
    bonus DOUBLE,
    PRIMARY KEY (emp_id, month)
);

-- 考勤表
CREATE TABLE attendance (
    emp_id INT,
    date VARCHAR(10),
    check_in VARCHAR(20),
    check_out VARCHAR(20)
);
```

- [ ] **步骤 11：运行冒烟验证进度**

运行：`uv run python data_builder/smoke_test.py; echo "exit=$?"`
预期：本任务 10 题全部 ✓；剩余失败仅任务 10 的 4 题：`['01_02', '04_02', '04_03', '04_04']`

- [ ] **步骤 12：Commit**

```bash
git add data_builder/manifest.py
git commit -m "fix: rewrite dialect-incompatible reference answers to MySQL 8"
```

---

### 任务 10：manifest 参考答案改写——伪占位 4 题可执行化 + 11_03 注释清理

**文件：**
- 修改：`data_builder/manifest.py`

把"承接上一问"式伪占位改写为完整可执行 SQL（保留步骤注释教学结构）。

- [ ] **步骤 1：01_02（行 119-127）替换为**

```sql
-- 承接 01_01 的思路：去重 → row_number 差值分组 → 按用户取最大连续天数
WITH dedup AS (
    SELECT id, SUBSTR(date, 1, 10) AS date
    FROM test
    GROUP BY id, SUBSTR(date, 1, 10)
),
numbered AS (
    SELECT id, date,
           ROW_NUMBER() OVER (PARTITION BY id ORDER BY date) AS rn
    FROM dedup
),
flagged AS (
    SELECT id, DATE_ADD(date, INTERVAL -rn DAY) AS date1
    FROM numbered
),
day_cnt AS (
    SELECT id, date1, COUNT(*) AS day_cnt
    FROM flagged
    GROUP BY id, date1
)
SELECT id, MAX(day_cnt) AS max_day_cnt
FROM day_cnt
GROUP BY id;
```

- [ ] **步骤 2：04_02（行 512-529）替换为**

```sql
-- 步骤一：进入+1，离开-1
SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
WHERE SUBSTR(login_time, 1, 8) = '20210310'
UNION ALL
SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
WHERE SUBSTR(logout_time, 1, 8) = '20210310';

-- 步骤二：按时间累加
SELECT room_id, event_time,
       SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
FROM (
    SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
    WHERE SUBSTR(login_time, 1, 8) = '20210310'
    UNION ALL
    SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    WHERE SUBSTR(logout_time, 1, 8) = '20210310'
) events;

-- 步骤三：取最大值
SELECT room_id, MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        WHERE SUBSTR(login_time, 1, 8) = '20210310'
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
        WHERE SUBSTR(logout_time, 1, 8) = '20210310'
    ) events
) online
GROUP BY room_id;
```

- [ ] **步骤 3：04_03（行 547-557）替换为**

```sql
-- 在步骤二的 event_time 上加 SUBSTR 取小时粒度即可
SELECT room_id, SUBSTR(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        WHERE SUBSTR(login_time, 1, 8) = '20210310'
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
        WHERE SUBSTR(logout_time, 1, 8) = '20210310'
    ) events
) online
GROUP BY room_id, SUBSTR(event_time, 1, 13);
```

- [ ] **步骤 4：04_04（行 574-580）替换为**

```sql
-- 去掉 WHERE 日期筛选即可
SELECT room_id, SUBSTR(event_time, 1, 13) AS hour_slot,
       MAX(online_cnt) AS max_online
FROM (
    SELECT room_id, event_time,
           SUM(user_type) OVER (PARTITION BY room_id ORDER BY event_time) AS online_cnt
    FROM (
        SELECT room_id, user_id, login_time AS event_time, 1 AS user_type FROM live_log
        UNION ALL
        SELECT room_id, user_id, logout_time AS event_time, -1 AS user_type FROM live_log
    ) events
) online
GROUP BY room_id, SUBSTR(event_time, 1, 13);
```

- [ ] **步骤 5：11_03（行 1103-1111，纯注释含 `||`）替换为**

```sql
-- year:  SUBSTR(date, 1, 4)
-- mm:    SUBSTR(date, 6, 2)
-- quarter: CONCAT(SUBSTR(date, 1, 4), 'Q', (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 3 + 1)
-- half:  CONCAT(SUBSTR(date, 1, 4), 'H', (CAST(SUBSTR(date, 6, 2) AS UNSIGNED) - 1) DIV 6 + 1)
-- ytm:   日期转 YYYYMM 格式
-- last12m: 最近12个月（date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)）
-- last30d/60d/90d/180d: 类似，用 DATE_SUB
```

- [ ] **步骤 6：运行冒烟，确认全绿**

运行：`uv run python data_builder/smoke_test.py; echo "exit=$?"`
预期 `exit=0`，失败: 无。统计应为 `{executable: 32, ddl: 1, comment_only: 4, stub: 7}`（合计 44；comment_only 为 01_04、06_03、10_01、11_03，ddl 为 10_02）

- [ ] **步骤 7：Commit**

```bash
git add data_builder/manifest.py
git commit -m "fix: make step-placeholder answers fully executable in MySQL"
```

---

### 任务 11：backend 迁移（database.py + 两个 router）

**文件：**
- 修改：`backend/database.py`（L4 import、L66、L87-124）
- 修改：`backend/routers/databases.py`（全文重写，26 行）
- 修改：`backend/routers/problems.py`（L1-9 import、L122-123、L141、L146、L154）
- 不动：`backend/routers/progress.py`、`categories.py`、`backend/main.py`

progress.db 的 `problems.db_path` 列**保留列名**，但存储值从绝对文件路径改为 schema 名（如 `01_continuous_login`）。`seed_problems()` 是 INSERT OR REPLACE，下次 `generate_data.py` 运行即自动刷新，无需手工迁移旧数据。

- [ ] **步骤 1：database.py 头部加 MySQL 常量与连接（放在现有 import 之后）**

```python
import pymysql
import pymysql.cursors

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "practice"


def get_practice_connection(schema: str | None = None) -> pymysql.connections.Connection:
    """获取练习库 MySQL 连接（DictCursor，便于直接输出 JSON）"""
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=schema,
        charset="utf8mb4", autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )


def get_schema_name(db_file: str) -> str:
    """manifest 的 db_file（如 01_continuous_login.db）→ MySQL schema 名"""
    schema = db_file[:-3] if db_file.endswith(".db") else db_file
    if not re.match(r"^[0-9a-z_]+$", schema):
        raise ValueError(f"Invalid schema name: {db_file}")
    return schema


def schema_exists(schema: str) -> bool:
    """检查练习 schema 是否已生成（容器未启动时返回 False 而不是抛错）"""
    try:
        conn = get_practice_connection()
    except pymysql.err.OperationalError:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (schema,),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def mysql_cli_command(schema: str) -> str:
    return f"mysql -h {MYSQL_HOST} -P {MYSQL_PORT} -u{MYSQL_USER} -p{MYSQL_PASSWORD} {schema}"


def mysql_jdbc_url(schema: str) -> str:
    return f"jdbc:mysql://{MYSQL_HOST}:{MYSQL_PORT}/{schema}"
```

- [ ] **步骤 2：database.py 的 seed_problems L66 改存 schema 名**

```python
                    prob.id, prob.category_id, prob.title, prob.difficulty,
                    cat.db_file[:-3],  # MySQL schema 名（列名沿用 db_path，避免迁移 progress.db）
```

- [ ] **步骤 3：database.py 删除 get_practice_db_path（L87-93），重写 get_table_schema（L96-124）**

```python
def get_table_schema(schema: str, table_name: str) -> dict:
    """读取指定 schema 中表的结构和前 5 行数据（MySQL）"""
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        return {}

    try:
        conn = get_practice_connection(schema)
    except pymysql.err.OperationalError:
        return {}
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                (schema, table_name),
            )
            columns = cur.fetchall()
            if not columns:
                return {}
            cur.execute(f"SELECT COUNT(*) AS cnt FROM `{table_name}`")
            row_count = cur.fetchone()["cnt"]
            cur.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
            rows = cur.fetchall()
    except pymysql.err.Error:
        return {}
    finally:
        conn.close()

    return {
        "name": table_name,
        "columns": [{"name": c["column_name"], "type": c["data_type"]} for c in columns],
        "row_count": row_count,
        "sample_rows": rows,
    }
```

- [ ] **步骤 4：routers/databases.py 全文替换**

```python
"""GET /api/databases/{id}/connect"""

from fastapi import APIRouter
from backend.database import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD,
    get_schema_name, schema_exists, mysql_cli_command, mysql_jdbc_url,
)

router = APIRouter()


@router.get("/databases/{category_id}/connect")
def get_connection(category_id: str):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import get_category

    cat = get_category(category_id)
    if not cat:
        return {"error": "Category not found"}

    schema = get_schema_name(cat.db_file)
    return {
        "db_file": cat.db_file,
        "schema": schema,
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "jdbc_url": mysql_jdbc_url(schema),
        "cli_command": mysql_cli_command(schema),
        "exists": schema_exists(schema),
    }
```

- [ ] **步骤 5：routers/problems.py 三处修改**

导入（L5-8）改为：

```python
from backend.database import (
    get_progress_connection, get_table_schema,
    mysql_cli_command, mysql_jdbc_url,
)
```

get_problem 端点（原 L122-123）：

```python
        "db_file": row["db_path"],
        "db_connection": mysql_cli_command(row["db_path"]),
        "jdbc_url": mysql_jdbc_url(row["db_path"]),
```

get_problem_tables 端点（原 L141、L146、L154）：

```python
    schema = row["db_path"]
    table_names = json.loads(row["table_names"]) if row["table_names"] else []

    tables = []
    for tname in table_names:
        info = get_table_schema(schema, tname)
        if info:
            tables.append(info)

    conn.close()

    return {
        "tables": tables,
        "db_connection": mysql_cli_command(schema),
        "jdbc_url": mysql_jdbc_url(schema),
    }
```

（注意：`get_table_schema` 现在第一个参数就是 schema 名，`db_path` 里存的已是 schema 名，直接传。）

- [ ] **步骤 6：重新生成数据（刷新 progress.db 中的 db_path 值）**

运行：`uv run python data_builder/generate_data.py`
预期：全绿

- [ ] **步骤 7：起后端并验证三个端点**

```bash
uv run uvicorn backend.main:app --port 8000 &
sleep 3
curl -s localhost:8000/api/databases/13/connect
curl -s localhost:8000/api/problems/13_01 | python3 -m json.tool | grep -A3 db_connection
curl -s localhost:8000/api/problems/13_01/tables | python3 -m json.tool | head -40
kill %1
```

预期：
- connect 返回 `"jdbc_url": "jdbc:mysql://127.0.0.1:3306/13_json_parsing"`、`"exists": true`
- db_connection 形如 `mysql -h 127.0.0.1 -P 3306 -uroot -ppractice 13_json_parsing`
- tables 返回 json_table 的列（id int、data text）、row_count 6、sample_rows 有数据

- [ ] **步骤 8：Commit**

```bash
git add backend/database.py backend/routers/databases.py backend/routers/problems.py
git commit -m "feat: backend serves MySQL connection info and table schemas"
```

---

### 任务 12：frontend 连接信息展示

**文件：**
- 修改：`frontend/src/types.ts`（L50、L71 附近）
- 修改：`frontend/src/pages/ProblemListPage.tsx`（L121-127 state、L150、L211-217、L305-336 渲染块）

- [ ] **步骤 1：types.ts 两处加字段**

`ProblemDetail` 接口（L38-51）内 `db_connection: string` 之后加一行：

```ts
  jdbc_url: string
```

`TablesResponse` 接口（L69-72）同样加：

```ts
  jdbc_url: string
```

- [ ] **步骤 2：ProblemListPage.tsx 加 state（L121 附近，紧随 dbConnection 声明）**

```tsx
  const [jdbcUrl, setJdbcUrl] = useState('')
```

以及 L127 `copied` 声明附近加：

```tsx
  const [copiedJdbc, setCopiedJdbc] = useState(false)
```

- [ ] **步骤 3：L150 处补充**

```tsx
      setDbConnection(t.db_connection)
      setJdbcUrl(t.jdbc_url)
```

- [ ] **步骤 4：L211-217 handleCopy 之后新增 handleCopyJdbc**

```tsx
  const handleCopyJdbc = () => {
    if (!jdbcUrl) return
    navigator.clipboard.writeText(jdbcUrl).then(() => {
      setCopiedJdbc(true)
      setTimeout(() => setCopiedJdbc(false), 2000)
    })
  }
```

- [ ] **步骤 5：替换 DbConnectionInfo 渲染块（L305-336）**

```tsx
            {/* DbConnectionInfo */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
              <div>
                <span className="text-xs text-gray-500 uppercase tracking-wide">Database (MySQL 8)</span>
                <p className="text-sm font-mono text-gray-700 mt-0.5">{detail.db_file}</p>
              </div>
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-8 shrink-0">CLI</span>
                  <p className="text-xs font-mono text-gray-500 truncate flex-1">{dbConnection}</p>
                  <button
                    onClick={handleCopy}
                    className="px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors shrink-0"
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 w-8 shrink-0">JDBC</span>
                  <p className="text-xs font-mono text-gray-400 truncate flex-1">{jdbcUrl}</p>
                  <button
                    onClick={handleCopyJdbc}
                    className="px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors shrink-0"
                  >
                    {copiedJdbc ? 'Copied' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>
```

- [ ] **步骤 6：类型检查**

运行：`cd frontend && npx tsc --noEmit && cd ..`
预期：无错误

- [ ] **步骤 7：Commit**

```bash
git add frontend/src/types.ts frontend/src/pages/ProblemListPage.tsx
git commit -m "feat: show MySQL CLI and JDBC connection info on problem page"
```

---

### 任务 13：start.sh 改造 + 冷启动验收

**文件：**
- 修改：`start.sh`

- [ ] **步骤 1：uv 检查之后（现 L17-20 与 L22-25 之间）插入 Docker 检查**

```bash
# 检查 Docker
if ! command -v docker &>/dev/null; then
    echo "❌ 未找到 docker，请先安装 Docker Desktop：https://www.docker.com/products/docker-desktop/"
    exit 1
fi
if ! docker info &>/dev/null; then
    echo "❌ Docker daemon 未运行，请先启动 Docker Desktop"
    exit 1
fi
```

- [ ] **步骤 2：替换数据生成段（现 L26-33）**

```bash
# 2. 启动 MySQL 并等待就绪
echo ""
echo "🐳 启动 MySQL 8 容器..."
docker compose up -d || {
    echo "❌ 容器启动失败——若为 3306 端口被占用，请停掉占用进程或修改 docker-compose.yml 的端口映射"
    exit 1
}
echo "⏳ 等待 MySQL 就绪..."
READY=0
for i in $(seq 1 60); do
    if docker compose exec -T mysql mysql -uroot -ppractice -e "SELECT 1" &>/dev/null; then
        READY=1
        break
    fi
    sleep 1
done
if [ "$READY" -ne 1 ]; then
    echo "❌ MySQL 健康检查超时（60s），请检查：docker compose logs mysql"
    exit 1
fi

# 3. 生成数据（幂等：每次重建 schema，progress.db 中的进度保留）
echo ""
echo "📦 生成练习数据..."
uv run python data_builder/generate_data.py
```

（后续步骤编号注释顺延即可，不必全局重排。）

- [ ] **步骤 3：冷启动验收**

```bash
docker compose down -v
bash start.sh
```

预期：容器重建 → healthy → 数据生成全绿 → 前后端启动 → `curl -s localhost:8000/api/health` 返回 ok。浏览器打开 http://localhost:5173 ：专题列表正常、任一题目详情显示 CLI/JDBC 两行连接信息（JDBC 指向 `13_json_parsing` 等 schema）、表结构与样例数据正常渲染、勾选完成/评分可用。验证后 Ctrl+C 停止。

- [ ] **步骤 4：Commit**

```bash
git add start.sh
git commit -m "feat: start.sh brings up MySQL container before data generation"
```

---

### 任务 14：手册与 README 口径更新

**文件：**
- 修改：`docs/sql-interview-review.md`（17 处 SQLite 标注，行号为当前行号）
- 修改：`README.md`、`README_zh.md`

- [ ] **步骤 1：手册关键行替换（逐行，新文本如下）**

| 行号 | 替换后文本 |
|---|---|
| 4 | `> 方言口径：MySQL 8（本地练习环境），Hive SQL 差异处单独标注。` |
| 53 | `\| 行转列（炸裂） \| Hive：\`lateral view explode(split(col, ','))\`；MySQL 8：\`JSON_TABLE\` / 递归 CTE \| Q15 \|` |
| 54 | `\| 列转行（聚合） \| Hive：\`concat_ws(',', collect_list(col))\`；MySQL 8：\`GROUP_CONCAT(col SEPARATOR ',')\` \| Q16 \|` |
| 95 | `6. **Hive 与 MySQL 差异**：\`date_add(d, n)\` 不是 \`INTERVAL\` 语法；Hive \`/\` 恒返回 double，MySQL \`/\` 同为小数除法（整除用 \`DIV\`）；多参取小都用 \`LEAST()\`；\`collect_list/collect_set\` vs \`GROUP_CONCAT\`；\`get_json_object\` vs \`JSON_EXTRACT\`。` |
| 496 | `- \`* 100.0\` 是关键：部分引擎（如 SQLite/Postgres）整数相除会截断（\`20 / 100 = 0\`）；Hive 与 MySQL 的 \`/\` 都返回小数（MySQL 中 \`20 / 100 = 0.2000\`），无截断问题。但 \`*100.0\` 写法跨方言稳健、无害，保留是好习惯。` |
| 958 | `> **MySQL/本地练习写法**（相关子查询版，O(n^2) 性能，部分 Hive 版本不支持子查询内 LIMIT）：` |
| 1218 | `> 📌 Hive 等价写法：将 \`DATE_ADD(a.first_date, INTERVAL 7 DAY)\` 替换为 Hive 的 \`date_add(a.first_date, 7)\`，其余逻辑完全相同。` |
| 1334 | `> 📌 MySQL 写法：\`SELECT user_id, GROUP_CONCAT(tag SEPARATOR ',') AS tags FROM user_tag_rows GROUP BY user_id;\`` |
| 1382 | `-- 注意：Hive 与 MySQL 的 / 都返回小数，整除必须分别用 div / DIV（如 3 月：(3-1)/3+1 = 1.666...，结果错误）` |
| 1387 | 不整行替换，只做两处**子串替换**：`（SQLite 用 \`CAST(... AS TEXT)\`）` → `（MySQL 用 \`CAST(... AS CHAR)\` 或 CONCAT 隐式转换）`；`**Hive 中整除必须用 \`div\`，\`/\` 恒返回 double**` → `**Hive/MySQL 中整除都必须用 div/DIV**`。行内其余文字保留。 |
| 1395 | `- **Hive vs MySQL 口径差异**：Hive 中整数转字符串用 \`cast(col as string)\`，MySQL 用 \`CAST(col AS CHAR)\` 或 CONCAT 隐式转换。功能等价，只是方言关键字不同。` |
| 1557 | `- **Q: Hive 里多参数取最小值用哪个函数？** A: \`LEAST(a, b, ...)\`，MySQL 同为 \`LEAST()\`。（SQLite 允许 \`MIN(a,b,...)\` 做标量多参取小，Hive/MySQL 严格区分 \`LEAST()\`（标量）和 \`MIN()\`（聚合）。）` |

保留不动：L1399（`quarter()` 函数的客观引擎对比，非本地口径断言）。

- [ ] **步骤 2：手册 4 处 "📌 SQLite 等价写法" 代码块（L1270、L1469、L1559-1561 附近）**

统一规则：标题行 `> 📌 SQLite 等价写法：` → `> 📌 MySQL 写法：`；块内 SQL 按 manifest 任务 9 的新版答案修正——具体地：
- L1270 块（explode 相关）：代码块替换为任务 9 步骤 4 的 08_01 递归 CTE 版本
- L1469、L1559-1561 块（MIN/LEAST 相关）：块内 SQLite 的多参 `MIN(a, b, ...)` → `LEAST(a, b, ...)`，注释 `-- SQLite 用 MIN() 替代 LEAST()` → `-- MySQL/Hive 直接用 LEAST()`

- [ ] **步骤 3：手册残留检查**

运行：`grep -n "SQLite" docs/sql-interview-review.md`
预期：剩余每一处都是客观引擎对比（如 L1399、L496 提及 SQLite 截断行为的对比句），不得再有"本项目本地 SQLite 即如此"式的本地口径断言，不得再有 `📌 SQLite 等价写法` 标题

- [ ] **步骤 4：README.md（英文）按下表替换**

| 行号 | 替换后文本 |
|---|---|
| 8 | `[![MySQL](https://img.shields.io/badge/MySQL-8-4479A1.svg)](https://www.mysql.com/)` |
| 18 | `- **Per-topic MySQL schemas** — open any topic in DBeaver and see only the relevant tables` |
| 29 | `\| **Offline capability** \| Requires internet \| **Fully local — MySQL 8 running in Docker on your machine** \|` |
| 55-57 | `- Python 3.12+` / `- Node.js 20+` / `- Docker Desktop (runs MySQL 8)` / `- [DBeaver](https://dbeaver.io/) (or any MySQL-compatible client)` |
| 65-66 | 保持 `bash start.sh`，其后补一行：`# First run pulls the mysql:8.4 image (~200MB) and generates practice data` |
| 72-73 | `# Generate data first` / `uv run python data_builder/generate_data.py` |
| 75-76 | `# Terminal 1: backend` / `uv run python -m uvicorn backend.main:app --port 8000` |
| 86 | `Open DBeaver → New Connection → MySQL → host 127.0.0.1, port 3306, user root, password practice, database <topic schema>. Write SQL, verify your results, then mark the problem as complete in the web dashboard.` |
| 88 | `The connection info (mysql CLI command + JDBC URL) is also displayed on each problem's detail page — click to copy.` |
| 94-95 | `│  data_builder │────▶│ MySQL (Docker) │◀────│   DBeaver    │` / `│  (Python)     │     │  (13 schemas)  │     │  (your SQL)  │` |
| 110 | `- **\`databases/\`** — \`progress.db\` for progress tracking (practice data lives in the MySQL Docker volume)` |
| 122 | `├── databases/                   # progress.db only, gitignored (practice data in MySQL)` |
| 125 | `│   ├── database.py              # progress.db management + MySQL practice-DB access` |

- [ ] **步骤 5：README_zh.md（中文）对称替换**

| 行号 | 替换后文本 |
|---|---|
| 8 | `[![MySQL](https://img.shields.io/badge/MySQL-8-4479A1.svg)](https://www.mysql.com/)` |
| 18 | `- **按专题独立的 MySQL schema** — 在 DBeaver 中打开只看到相关表，零干扰` |
| 29 | `\| **离线可用** \| 需要网络 \| **纯本地 — MySQL 8 跑在你机器上的 Docker 里** \|` |
| 53-57 | `- Python 3.12+` / `- Node.js 20+` / `- Docker Desktop（运行 MySQL 8）` / `- [DBeaver](https://dbeaver.io/)（或其他支持 MySQL 的客户端）` |
| 65-66 | 保持 `bash start.sh`，其后补一行：`# 首次运行会拉取 mysql:8.4 镜像（约 200MB）并生成练习数据` |
| 72-73 | `# 先生成数据` / `uv run python data_builder/generate_data.py` |
| 75-76 | `# 终端1：后端` / `uv run python -m uvicorn backend.main:app --port 8000` |
| 86 | `打开 DBeaver → 新建连接 → MySQL → 主机 127.0.0.1，端口 3306，用户 root，密码 practice，数据库 <专题 schema>。写 SQL、验证结果，然后在 Web 后台标记该题完成。` |
| 88 | `每道题的详情页也显示了连接信息（mysql 命令行 + JDBC URL），支持一键复制。` |
| 94-95 | `│  data_builder │────▶│ MySQL (Docker) │◀────│   DBeaver    │` / `│  (Python)     │     │  (13 个 schema) │     │  (你写 SQL)  │` |
| 110 | `- **\`databases/\`** — \`progress.db\`（进度追踪；练习数据在 MySQL Docker 卷中）` |
| 122 | `├── databases/                   # 仅 progress.db（gitignore；练习数据在 MySQL）` |
| 125 | `│   ├── database.py              # progress.db 管理 + MySQL 练习库访问` |

- [ ] **步骤 6：Commit**

```bash
git add docs/sql-interview-review.md README.md README_zh.md
git commit -m "docs: align handbook and READMEs with MySQL 8 practice environment"
```

---

### 任务 15：最终验收（规格 §7 全项）

**文件：** 无新改动（只验证；发现问题回对应任务修复）

- [ ] **步骤 1：容器与 schema**

```bash
docker compose down -v && docker compose up -d
# 等 30 秒后：
docker compose exec -T mysql mysql -uroot -ppractice -N -e "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name LIKE '0%' OR schema_name LIKE '1%'"
```
预期：`13`

- [ ] **步骤 2：冒烟全绿**

运行：`uv run python data_builder/smoke_test.py; echo "exit=$?"`
预期：`exit=0`，失败: 无

- [ ] **步骤 3：冷启动一键跑通**

运行：`docker compose down -v && bash start.sh`
预期：全流程无报错，前端 5173 / 后端 8000 就绪（验收后 Ctrl+C）

- [ ] **步骤 4：前端功能回归（手动）**

浏览器逐项确认：专题列表统计、题目详情（CLI/JDBC 连接信息、表结构、样例数据）、标记完成、掌握度评分、笔记。

- [ ] **步骤 5：手册口径终检**

运行：`grep -n "SQLite" docs/sql-interview-review.md README.md README_zh.md`
预期：README 两份零命中；手册剩余仅为客观引擎对比句

- [ ] **步骤 6：DBeaver 实连（手动，用户参与）**

DBeaver 新建 MySQL 连接（127.0.0.1:3306, root/practice），打开 `01_continuous_login` schema，执行：
```sql
SELECT id, SUBSTR(date, 1, 10) AS date
FROM test LIMIT 5;
```
以及 13_01 的 `JSON_TABLE` 答案（任务 9 步骤 7）确认可跑。

- [ ] **步骤 7：收尾 commit（如有零星修复）并汇报验收结果**

```bash
git status --short   # 应干净（或仅剩与本计划无关的文件）
```
