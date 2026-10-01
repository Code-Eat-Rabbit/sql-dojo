# 页内 SQL 执行与自动判题 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 在题目页面内编写并只读执行 SQL（连 Docker MySQL），「提交答案」将用户结果与参考答案比对自动判题，判对触发现有完成+自评流程；SQL 草稿按题持久化到 progress.db。

**架构：** 扩展现有 FastAPI 后端（方案 A）：新增 `backend/sql_executor.py`（白名单 + READ ONLY 会话 + 超时 + 行数上限）、`backend/grader.py`（归一化比对）、`backend/routers/execute.py`（execute/submit/draft 端点）；前端新增 `SQLWorkspace`（CodeMirror 6）与通用 `ResultTable`，集成进 ProblemListPage。规格见 `docs/superpowers/specs/2026-10-01-in-app-sql-execution-design.md`。

**技术栈：** Python 3.11+ / FastAPI / PyMySQL / SQLite(progress.db) / pytest / React 19 / @uiw/react-codemirror + @codemirror/lang-sql / Tailwind 4

**与规格的两点说明：**

1. 判题比对为「用户**最后一个**结果集 匹配参考答案**任一**结果集即判对」。规格只写了行多重集相等；但 manifest 存在多解汇总题（如 `01_03` 三种方法连发三个 SELECT，参考答案最后一个结果集只是其中一种解法），严格比对"最后集合"会把正确解法误判为错。
2. 其余完全按规格，submit 仅返回 `{correct, diffSummary}` 不附带结果集。

**前置条件（每个任务开始前确认）：**

- MySQL 容器在跑：`docker ps --filter name=sql-dojo-mysql`（不在则 `bash start.sh` 或 `docker compose up -d && uv run python data_builder/generate_data.py`）
- 在隔离 worktree 中执行本计划（using-git-worktrees）；worktree 中需 `uv sync` 与 `cd frontend && npm install`
- 集成测试用 TestClient 进程内调用，不占用 8000 端口，与主工作区正在运行的服务不冲突

---

## 文件结构

| 文件 | 操作 | 职责 |
|---|---|---|
| `backend/sql_executor.py` | 创建 | 拆句/白名单/大小限制；只读会话执行；错误转译；`is_gradable_sql` |
| `backend/grader.py` | 创建 | 值归一化 + 结果集比对（顺序敏感/不敏感、多解任一匹配） |
| `backend/routers/execute.py` | 创建 | `POST execute` / `POST submit` / `GET+PUT draft` |
| `backend/models/schemas.py` | 修改 | 新增 `SqlRequest` / `DraftRequest` |
| `backend/main.py` | 修改 | 挂载 execute 路由（main.py:11、23-26 一带） |
| `backend/database.py` | 修改 | `init_progress_db` 建 `drafts` 表 + 幂等加列；`seed_problems` 写 gradable/ordered（database.py:66-129） |
| `backend/routers/problems.py` | 修改 | `get_problem` 响应增加 `gradable`（problems.py:107-126） |
| `data_builder/manifest.py` | 修改 | `Problem` 增加 `ordered: bool = False`（manifest.py:11-34） |
| `tests/backend/conftest.py` | 创建 | `tmp_progress_db` / `client` fixtures |
| `tests/backend/test_health.py` | 创建 | TestClient 冒烟 |
| `tests/backend/test_sql_executor.py` | 创建 | 拆句/白名单/大小限制单元测试 |
| `tests/backend/test_sql_executor_integration.py` | 创建 | 真实 MySQL 执行/只读/超时/截断集成测试 |
| `tests/backend/test_grader.py` | 创建 | 归一化与比对单元测试 |
| `tests/backend/test_seed.py` | 创建 | gradable 标记与 drafts 表迁移测试 |
| `tests/backend/test_execute_api.py` | 创建 | 端点集成测试（TestClient + 真实 MySQL） |
| `frontend/src/types.ts` | 修改 | `ProblemDetail.gradable`、`SqlExecuteResult` 等 |
| `frontend/src/api.ts` | 修改 | `executeSql` / `submitSql` / `getDraft` / `saveDraft` |
| `frontend/src/components/ResultTable.tsx` | 创建 | 通用结果表格（列名+可选类型、数组行） |
| `frontend/src/components/SQLWorkspace.tsx` | 创建 | 编辑器 + 运行/提交 + 结果 + 反馈 + 草稿 |
| `frontend/src/pages/ProblemListPage.tsx` | 修改 | 插入 SQLWorkspace；样例数据表改用 ResultTable |
| `frontend/package.json` | 修改 | 新增两个 CodeMirror 依赖 |
| `README.md` / `README_zh.md` | 修改 | 练习流程改为页内执行为主、DBeaver 为辅 |
| `pyproject.toml` | 修改 | dev 依赖 pytest；pytest pythonpath/testpaths 配置 |

---

### 任务 1：pytest 基础设施

**文件：**
- 修改：`pyproject.toml`
- 创建：`tests/backend/test_health.py`

- [ ] **步骤 1：安装 pytest 并配置路径解析**

```bash
uv add --dev pytest
```

`pyproject.toml` 的 `[dependency-groups] dev` 变为 `dev = ["pytest>=..."]`。然后在其后追加：

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

（`pythonpath` 使 `import backend.*` 在 pytest 下可用；TestClient 所需的 httpx 已随 `fastapi[standard]` 安装，若步骤 3 报缺 httpx 再 `uv add --dev httpx`。）

- [ ] **步骤 2：编写冒烟测试**

`tests/backend/test_health.py`：

```python
"""TestClient 冒烟：应用可导入、health 端点可用"""


def test_health():
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

- [ ] **步骤 3：运行验证通过**

运行：`uv run pytest -v`
预期：`test_health PASSED`，1 passed。

- [ ] **步骤 4：Commit**

```bash
git add pyproject.toml uv.lock tests/backend/test_health.py
git commit -m "chore: add pytest infrastructure with app smoke test"
```

---

### 任务 2：sql_executor — 拆句 / 白名单 / 大小限制（纯单元）

**文件：**
- 创建：`backend/sql_executor.py`
- 测试：`tests/backend/test_sql_executor.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_sql_executor.py`：

```python
"""sql_executor 纯单元：拆句、白名单、大小限制（不连 MySQL）"""

import pytest

from backend.sql_executor import (
    SqlRejectedError,
    assert_executable,
    is_gradable_sql,
    split_statements,
)


def test_split_statements_strips_comments_and_blanks():
    sql = "-- 查询\nSELECT 1;\n\nSELECT 2; -- tail\n"
    assert split_statements(sql) == ["SELECT 1", "SELECT 2"]


def test_assert_executable_accepts_readonly_verbs():
    for s in [
        "SELECT 1",
        "with t as (select 1) select * from t",  # 小写也接受
        "SHOW TABLES",
        "DESC scores",
        "DESCRIBE scores",
        "EXPLAIN SELECT 1",
    ]:
        assert assert_executable(s)  # 不抛错即通过


def test_assert_executable_rejects_writes():
    for s in [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET a = 1",
        "DELETE FROM t",
        "CREATE TABLE x (id INT)",
        "DROP TABLE t",
        "TRUNCATE TABLE t",
    ]:
        with pytest.raises(SqlRejectedError) as ei:
            assert_executable(s)
        assert ei.value.code == "forbidden_statement"


def test_assert_executable_rejects_write_in_later_statement():
    with pytest.raises(SqlRejectedError):
        assert_executable("SELECT 1; DELETE FROM t")


def test_assert_executable_rejects_empty_and_oversize():
    with pytest.raises(SqlRejectedError) as ei:
        assert_executable("-- 只有注释")
    assert ei.value.code == "empty_sql"

    with pytest.raises(SqlRejectedError) as ei:
        assert_executable("SELECT '" + "x" * (64 * 1024) + "'")
    assert ei.value.code == "sql_too_large"


def test_is_gradable_sql():
    assert is_gradable_sql("SELECT 1 FROM t;") is True
    assert is_gradable_sql("WITH x AS (SELECT 1) SELECT * FROM x") is True
    assert is_gradable_sql("CREATE TABLE a (id INT);") is False
    assert is_gradable_sql("-- 说明题\n没有可执行语句") is False
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_sql_executor.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'backend.sql_executor'`

- [ ] **步骤 3：编写实现**

`backend/sql_executor.py`（本任务只写纯函数部分，执行部分任务 3 追加到同一文件）：

```python
"""只读 SQL 执行器：白名单校验 + 只读会话 + 超时 + 行数上限"""

import time

import pymysql

from backend.database import get_practice_connection

MAX_SQL_BYTES = 64 * 1024
MAX_ROWS = 500
DEFAULT_TIMEOUT_MS = 5000
READONLY_VERBS = {"SELECT", "WITH", "SHOW", "DESC", "DESCRIBE", "EXPLAIN"}


class SqlRejectedError(Exception):
    """请求被白名单/大小/空语句拒绝（HTTP 400）"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class MysqlUnavailableError(Exception):
    """MySQL 不可连接（HTTP 503）"""

    def __init__(self, message: str = "MySQL 未启动，请先运行 bash start.sh"):
        self.message = message
        super().__init__(message)


class MysqlExecutionError(Exception):
    """MySQL 执行报错（HTTP 400），message 已转译为友好中文"""

    def __init__(self, mysql_code: int, message: str):
        self.mysql_code = mysql_code
        self.message = message
        super().__init__(message)


def strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        cut = line.find("--")
        lines.append(line if cut == -1 else line[:cut])
    return "\n".join(lines)


def split_statements(sql: str) -> list[str]:
    return [s.strip() for s in strip_comments(sql).split(";") if s.strip()]


def _first_verb(stmt: str) -> str:
    return stmt.split(None, 1)[0].upper()


def assert_executable(sql: str) -> list[str]:
    """大小校验 + 白名单校验，返回语句列表；不合规抛 SqlRejectedError"""
    if len(sql.encode("utf-8")) > MAX_SQL_BYTES:
        raise SqlRejectedError(
            "sql_too_large", f"SQL 超过 {MAX_SQL_BYTES // 1024}KB 上限")
    stmts = split_statements(sql)
    if not stmts:
        raise SqlRejectedError("empty_sql", "没有可执行的 SQL 语句")
    for s in stmts:
        if _first_verb(s) not in READONLY_VERBS:
            raise SqlRejectedError(
                "forbidden_statement",
                f"只允许查询语句（SELECT/WITH/SHOW/DESC/EXPLAIN），"
                f"已拒绝：{_first_verb(s)}",
            )
    return stmts


def is_gradable_sql(sql: str) -> bool:
    """参考答案是否全为查询语句（seed 时用于 gradable 标记）"""
    stmts = split_statements(sql)
    return bool(stmts) and all(_first_verb(s) in READONLY_VERBS for s in stmts)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_sql_executor.py -v`
预期：6 passed

- [ ] **步骤 5：Commit**

```bash
git add backend/sql_executor.py tests/backend/test_sql_executor.py
git commit -m "feat: readonly SQL whitelist and statement splitting"
```

---

### 任务 3：sql_executor — 只读会话执行与错误转译（集成 MySQL）

**文件：**
- 修改：`backend/sql_executor.py`（追加执行部分）
- 测试：`tests/backend/test_sql_executor_integration.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_sql_executor_integration.py`：

```python
"""sql_executor 集成：连接真实 MySQL 容器执行"""

import pytest

from backend.database import schema_exists
from backend.sql_executor import (
    MysqlExecutionError,
    MysqlUnavailableError,
    execute_statements,
    run_readonly,
)

pytestmark = pytest.mark.skipif(
    not schema_exists("01_continuous_login"),
    reason="MySQL 容器未运行（先 bash start.sh）",
)


def test_run_readonly_select():
    r = run_readonly("01_continuous_login", "SELECT id FROM test LIMIT 3")
    assert r["columns"] == ["id"]
    assert r["rowCount"] == 3
    assert len(r["rows"]) == 3
    assert r["truncated"] is False
    assert r["elapsedMs"] >= 0


def test_multi_statement_returns_last_result_set():
    r = run_readonly("01_continuous_login", "SELECT 1 AS a; SELECT 2 AS b;")
    assert r["columns"] == ["b"]
    assert r["rows"] == [[2]]


def test_row_cap_marks_truncated():
    parts = ["SELECT 1 AS n"] + [f"SELECT {i}" for i in range(2, 602)]  # 601 行
    r = run_readonly("01_continuous_login", " UNION ALL ".join(parts))
    assert r["rowCount"] == 500
    assert r["truncated"] is True


def test_write_bypassing_whitelist_rejected_by_readonly():
    # WITH 通过白名单，但 READ ONLY 会话拒绝写操作（MySQL 错误 1792）
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly(
            "01_continuous_login",
            "WITH t AS (SELECT 1 AS x) UPDATE test SET id = id",
        )
    assert ei.value.mysql_code == 1792
    assert "只允许查询语句" in ei.value.message


def test_syntax_error_translated():
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly("01_continuous_login", "SELECT FROM WHERE")
    assert ei.value.mysql_code == 1064
    assert "语法错误" in ei.value.message


def test_timeout_raises():
    # 4 维自交叉积必然超过 1s，触发 max_execution_time（错误 3024）
    sql = ("SELECT COUNT(*) FROM attendance a, attendance b, "
           "attendance c, attendance d")
    with pytest.raises(MysqlExecutionError) as ei:
        run_readonly("10_hr_warehouse", sql, timeout_ms=1000)
    assert ei.value.mysql_code == 3024


def test_mysql_unavailable(monkeypatch):
    import backend.database as db

    monkeypatch.setattr(db, "MYSQL_PORT", 59999)
    with pytest.raises(MysqlUnavailableError):
        run_readonly("01_continuous_login", "SELECT 1")


def test_execute_statements_keeps_raw_values():
    # 判题用原始值（不经 JSON 转换），execute_statements 直接暴露
    sets = execute_statements("03_window_rank", ["SELECT score FROM scores LIMIT 1"])
    assert sets[0]["columns"] == ["score"]
    assert len(sets[0]["rows"]) == 1
    from decimal import Decimal
    assert isinstance(sets[0]["rows"][0][0], (int, float, Decimal))  # 原生数值
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_sql_executor_integration.py -v`
预期：FAIL，`ImportError: cannot import name 'execute_statements'`

- [ ] **步骤 3：在 `backend/sql_executor.py` 追加执行部分**

在文件末尾追加（并把文件顶部 `import time` 补上 `import datetime as _dt` 与 `from decimal import Decimal`）：

```python
import datetime as _dt
from decimal import Decimal


def _translate_error(e: pymysql.err.Error) -> MysqlExecutionError:
    code = e.args[0] if e.args else 0
    detail = str(e.args[1]) if len(e.args) > 1 else str(e)
    if code == 1792:  # ER_CANT_EXECUTE_IN_READ_ONLY_TRANSACTION
        msg = "只允许查询语句：当前会话为只读（READ ONLY）"
    elif code == 1064:  # ER_PARSE_ERROR
        msg = f"SQL 语法错误：{detail}"
    elif code == 3024:  # ER_QUERY_TIMEOUT
        msg = "执行超时（受 max_execution_time 限制），请优化查询"
    elif code == 1146:  # ER_NO_SUCH_TABLE
        msg = f"表不存在：{detail}"
    else:
        msg = detail
    return MysqlExecutionError(code, msg)


def execute_statements(schema: str, stmts: list[str],
                       timeout_ms: int = DEFAULT_TIMEOUT_MS) -> list[dict]:
    """在只读会话中依次执行语句，返回全部结果集（原始值，判题用）。

    每个结果集：{"columns": list[str], "rows": list[tuple], "truncated": bool}
    行数上限 MAX_ROWS=500，两侧（用户/参考）同一上限保证判题公平。
    """
    try:
        conn = get_practice_connection(schema)
    except pymysql.err.OperationalError as e:
        raise MysqlUnavailableError() from e
    try:
        cur = conn.cursor(pymysql.cursors.Cursor)  # 数组行（非 Dict）
        cur.execute("SET SESSION TRANSACTION READ ONLY")
        cur.execute(f"SET SESSION max_execution_time = {int(timeout_ms)}")
        results = []
        for stmt in stmts:
            try:
                cur.execute(stmt)
            except pymysql.err.Error as e:
                raise _translate_error(e) from e
            if cur.description:
                rows = cur.fetchmany(MAX_ROWS + 1)
                results.append({
                    "columns": [d[0] for d in cur.description],
                    "rows": rows[:MAX_ROWS],
                    "truncated": len(rows) > MAX_ROWS,
                })
        return results
    finally:
        conn.close()


def _json_safe(v):
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", "replace")
    if isinstance(v, (Decimal, _dt.datetime, _dt.date, _dt.timedelta, _dt.time)):
        return str(v)
    return v


def run_readonly(schema: str, sql: str,
                 timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    """校验 + 执行，返回最后一个结果集（JSON 安全，API 展示用）"""
    stmts = assert_executable(sql)
    t0 = time.perf_counter()
    results = execute_statements(schema, stmts, timeout_ms=timeout_ms)
    elapsed = int((time.perf_counter() - t0) * 1000)
    if not results:
        return {"columns": [], "rows": [], "rowCount": 0,
                "truncated": False, "elapsedMs": elapsed}
    last = results[-1]
    return {
        "columns": last["columns"],
        "rows": [[_json_safe(v) for v in row] for row in last["rows"]],
        "rowCount": len(last["rows"]),
        "truncated": last["truncated"],
        "elapsedMs": elapsed,
    }
```

注意：`import pymysql.cursors` 需在文件顶部（任务 2 已 `import pymysql`，改为 `import pymysql.cursors` 或直接用字符串 `pymysql.cursors.Cursor` 前 import）。顶部 import 区最终为：

```python
import datetime as _dt
import time
from decimal import Decimal

import pymysql.cursors

from backend.database import get_practice_connection
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_sql_executor_integration.py -v`
预期：8 passed（timeout 用例约耗时 1-2 秒）

- [ ] **步骤 5：Commit**

```bash
git add backend/sql_executor.py tests/backend/test_sql_executor_integration.py
git commit -m "feat: readonly MySQL execution with timeout, row cap and error translation"
```

---

### 任务 4：grader — 归一化与比对（纯单元）

**文件：**
- 创建：`backend/grader.py`
- 测试：`tests/backend/test_grader.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_grader.py`：

```python
"""grader：值归一化与结果集比对"""

import datetime as dt
from decimal import Decimal

from backend.grader import grade, normalize_value


def set_(cols, rows):
    return {"columns": list(cols), "rows": [tuple(r) for r in rows],
            "truncated": False}


def test_normalize_numeric_equivalence():
    assert normalize_value(1) == normalize_value(Decimal("1.0"))
    assert normalize_value(0.1) == normalize_value(Decimal("0.10"))
    assert normalize_value(None) != normalize_value("")
    assert normalize_value(None) != normalize_value(0)
    assert normalize_value(b"ab") == normalize_value("ab")
    assert normalize_value(dt.datetime(2026, 10, 1, 0, 0)) == \
        normalize_value(dt.datetime(2026, 10, 1, 0, 0))


def test_correct_order_insensitive():
    user = set_(["a", "b"], [[1, "x"], [2, "y"]])
    ref = set_(["c", "d"], [[2, "y"], [1, "x"]])  # 列名不参与，顺序打乱
    assert grade(user, [ref]) == {"correct": True, "diffSummary": None}


def test_column_count_mismatch():
    r = grade(set_(["a"], [[1]]), [set_(["a", "b"], [[1, 2]])])
    assert r["correct"] is False
    assert "列数不符" in r["diffSummary"]


def test_missing_and_extra_rows():
    r = grade(set_(["a"], [[1], [1], [3]]), [set_(["a"], [[1], [2]])])
    assert r["correct"] is False
    assert "缺 1 行" in r["diffSummary"]
    assert "多 1 行" in r["diffSummary"]


def test_ordered_mode_checks_sequence():
    ref = set_(["a"], [[1], [2], [3]])
    shuffled = set_(["a"], [[3], [1], [2]])
    assert grade(shuffled, [ref], ordered=True)["correct"] is False
    assert grade(shuffled, [ref], ordered=False)["correct"] is True


def test_matches_any_reference_solution():
    # 多解汇总题：匹配任一参考结果集即判对
    method1 = set_(["user_id"], [[1], [3]])
    method2 = set_(["uid"], [[7], [9], [2]])
    user = set_(["x"], [[7], [2], [9]])
    assert grade(user, [method1, method2])["correct"] is True
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_grader.py -v`
预期：FAIL，`ModuleNotFoundError: No module named 'backend.grader'`

- [ ] **步骤 3：编写实现**

`backend/grader.py`：

```python
"""判题：用户末个结果集与参考答案各结果集的归一化比对"""

import datetime as dt
from collections import Counter
from decimal import Decimal


def normalize_value(v):
    """归一化为可哈希的类型标签值，消除表示差异（1 vs 1.0、b'a' vs 'a'）"""
    if v is None:
        return ("null", "")
    if isinstance(v, bool):
        return ("num", Decimal(int(v)))
    if isinstance(v, (int, float, Decimal)):
        return ("num", Decimal(str(v)))
    if isinstance(v, (bytes, bytearray)):
        return ("str", v.decode("utf-8", "replace"))
    if isinstance(v, dt.datetime):
        return ("dt", v.isoformat(" "))
    if isinstance(v, dt.date):
        return ("dt", v.isoformat())
    return ("str", str(v))


def _row_key(row) -> tuple:
    return tuple(normalize_value(v) for v in row)


def _multiset(rows) -> Counter:
    return Counter(_row_key(r) for r in rows)


def grade(user: dict, reference_sets: list[dict], ordered: bool = False) -> dict:
    """user 为用户最后一个结果集；reference_sets 为参考答案全部结果集。

    默认：列数相等 + 行多重集相等（顺序不敏感，列名不参与）。
    ordered=True：按行序列严格比对。
    匹配任一参考结果集即判对（多解汇总题）。
    """
    fallback = None
    for ref in reference_sets:
        if len(ref["columns"]) != len(user["columns"]):
            fallback = fallback or (
                f"列数不符（期望 {len(ref['columns'])} 列，"
                f"实际 {len(user['columns'])} 列）"
            )
            continue
        if ordered:
            if [_row_key(r) for r in user["rows"]] == \
                    [_row_key(r) for r in ref["rows"]]:
                return {"correct": True, "diffSummary": None}
            fallback = fallback or "行顺序不一致"
            continue
        miss = sum((_multiset(ref["rows"]) - _multiset(user["rows"])).values())
        extra = sum((_multiset(user["rows"]) - _multiset(ref["rows"])).values())
        if miss == 0 and extra == 0:
            return {"correct": True, "diffSummary": None}
        parts = []
        if miss:
            parts.append(f"缺 {miss} 行")
        if extra:
            parts.append(f"多 {extra} 行")
        fallback = fallback or " / ".join(parts)
    return {"correct": False, "diffSummary": fallback}
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_grader.py -v`
预期：6 passed

- [ ] **步骤 5：Commit**

```bash
git add backend/grader.py tests/backend/test_grader.py
git commit -m "feat: result set grading with normalization and multi-solution match"
```

---

### 任务 5：manifest `ordered` 字段 + progress.db 迁移与 seed

**文件：**
- 修改：`data_builder/manifest.py:11-34`（Problem dataclass）
- 修改：`backend/database.py:66-129`（init_progress_db / seed_problems）
- 创建：`tests/backend/conftest.py`
- 测试：`tests/backend/test_seed.py`

- [ ] **步骤 1：创建 conftest 与失败测试**

`tests/backend/conftest.py`：

```python
"""共享 fixtures：隔离的 progress.db + TestClient"""

import pytest


@pytest.fixture()
def tmp_progress_db(tmp_path, monkeypatch):
    """临时 progress.db：init + seed，不触碰真实 databases/progress.db"""
    import backend.database as db

    fake = tmp_path / "progress.db"
    monkeypatch.setattr(db, "PROGRESS_DB", fake)
    db.init_progress_db()
    db.seed_problems()
    yield fake


@pytest.fixture()
def client(tmp_progress_db):
    from fastapi.testclient import TestClient
    from backend.main import app

    return TestClient(app)
```

`tests/backend/test_seed.py`：

```python
"""seed 迁移：gradable/ordered 列 + drafts 表"""

import sqlite3


def test_seed_marks_gradable(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    rows = dict(conn.execute("SELECT id, gradable FROM problems").fetchall())
    conn.close()
    assert rows["01_01"] == 1   # 查询题可判题
    assert rows["01_04"] == 0   # 总结题（纯注释）不可判题
    assert rows["10_01"] == 0   # 说明题不可判题
    assert rows["10_02"] == 0   # DDL 建表题不可判题


def test_ordered_column_defaults_zero(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    val = conn.execute(
        "SELECT ordered FROM problems WHERE id = '01_01'").fetchone()[0]
    conn.close()
    assert val == 0


def test_drafts_table_created(tmp_progress_db):
    conn = sqlite3.connect(tmp_progress_db)
    conn.execute(
        "INSERT INTO drafts (problem_id, sql_text, updated_at) "
        "VALUES ('01_01', 'SELECT 1', '2026-10-01')")
    conn.commit()
    val = conn.execute(
        "SELECT sql_text FROM drafts WHERE problem_id = '01_01'").fetchone()[0]
    conn.close()
    assert val == "SELECT 1"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_seed.py -v`
预期：FAIL，`sqlite3.OperationalError: no such column: gradable`

- [ ] **步骤 3：实现三处修改**

(a) `data_builder/manifest.py` — Problem dataclass 的 `hints` 字段后追加：

```python
    hints: List[str]
    ordered: bool = False        # 判题是否要求行顺序一致（默认多重集比对）
```

（docstring 的 Attributes 段补一行：`ordered: 判题是否要求行顺序一致。`；现有构造均为关键字参数，默认值不影响。）

(b) `backend/database.py` — 顶部 import 区追加：

```python
from backend.sql_executor import is_gradable_sql
```

`init_progress_db` 的 executescript 末尾追加 drafts 表，并在 with 块末尾追加幂等加列：

```python
def init_progress_db():
    """创建 progress.db 及 problems/progress/drafts 表"""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(PROGRESS_DB)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS problems (
                id TEXT PRIMARY KEY,
                category_id TEXT NOT NULL,
                title TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                db_path TEXT NOT NULL,
                table_names TEXT DEFAULT '[]',
                description TEXT DEFAULT '',
                reference_sql TEXT DEFAULT '',
                hints TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS progress (
                problem_id TEXT PRIMARY KEY REFERENCES problems(id),
                status TEXT DEFAULT 'not_started',
                completed_count INTEGER DEFAULT 0,
                mastery_level INTEGER DEFAULT 0,
                last_practiced_at TIMESTAMP,
                notes TEXT DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS drafts (
                problem_id TEXT PRIMARY KEY REFERENCES problems(id),
                sql_text TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );
        """)
        # 老库幂等升级：problems 增加 gradable / ordered
        for col in ("gradable", "ordered"):
            try:
                conn.execute(
                    f"ALTER TABLE problems ADD COLUMN {col} "
                    f"INTEGER NOT NULL DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # 列已存在
```

(c) `backend/database.py` — `seed_problems` 的 INSERT 改为：

```python
                conn.execute("""
                    INSERT OR REPLACE INTO problems
                        (id, category_id, title, difficulty, db_path, table_names,
                         description, reference_sql, hints, tags, gradable, ordered)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prob.id, prob.category_id, prob.title, prob.difficulty,
                    cat.db_file[:-3],  # MySQL schema 名（列名沿用 db_path）
                    json.dumps(prob.tables, ensure_ascii=False),
                    prob.description.strip(),
                    prob.reference_sql.strip(),
                    json.dumps(prob.hints, ensure_ascii=False),
                    json.dumps(prob.tags, ensure_ascii=False),
                    1 if is_gradable_sql(prob.reference_sql) else 0,
                    1 if prob.ordered else 0,
                ))
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_seed.py -v`
预期：3 passed

- [ ] **步骤 5：Commit**

```bash
git add data_builder/manifest.py backend/database.py tests/backend/conftest.py tests/backend/test_seed.py
git commit -m "feat: seed problems with gradable/ordered flags and drafts table"
```

---

### 任务 6：execute / submit / draft 路由

**文件：**
- 修改：`backend/models/schemas.py`（末尾追加模型）
- 创建：`backend/routers/execute.py`
- 修改：`backend/main.py`（挂载路由）
- 测试：`tests/backend/test_execute_api.py`

- [ ] **步骤 1：编写失败的测试**

`tests/backend/test_execute_api.py`：

```python
"""execute/submit/draft 端点集成（TestClient + 真实 MySQL）"""

import pytest

from backend.database import schema_exists

pytestmark = pytest.mark.skipif(
    not schema_exists("01_continuous_login"),
    reason="MySQL 容器未运行（先 bash start.sh）",
)


def test_execute_ok(client):
    r = client.post("/api/problems/01_01/execute",
                    json={"sql": "SELECT id FROM test LIMIT 3"})
    assert r.status_code == 200
    data = r.json()
    assert data["columns"] == ["id"]
    assert data["rowCount"] == 3


def test_execute_rejects_write(client):
    r = client.post("/api/problems/01_01/execute",
                    json={"sql": "DELETE FROM test"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "forbidden_statement"


def test_execute_mysql_down_503(client, monkeypatch):
    import backend.database as db

    monkeypatch.setattr(db, "MYSQL_PORT", 59999)
    r = client.post("/api/problems/01_01/execute", json={"sql": "SELECT 1"})
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "mysql_unavailable"


def test_execute_unknown_problem_404(client):
    r = client.post("/api/problems/nope/execute", json={"sql": "SELECT 1"})
    assert r.status_code == 404


def test_submit_correct_with_reference_sql(client):
    ref = client.get("/api/problems/01_01").json()["reference_sql"]
    r = client.post("/api/problems/01_01/submit", json={"sql": ref})
    assert r.status_code == 200
    assert r.json()["correct"] is True


def test_submit_wrong_reports_diff(client):
    r = client.post("/api/problems/01_01/submit",
                    json={"sql": "SELECT 1 AS one"})
    assert r.status_code == 200
    body = r.json()
    assert body["correct"] is False
    assert body["diffSummary"]


def test_submit_rejects_non_gradable(client):
    r = client.post("/api/problems/10_02/submit", json={"sql": "SELECT 1"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "not_gradable"


def test_draft_roundtrip(client):
    assert client.get("/api/problems/01_01/draft").json() == {"sql": ""}
    r = client.put("/api/problems/01_01/draft", json={"sql": "SELECT 1"})
    assert r.status_code == 204
    assert client.get("/api/problems/01_01/draft").json() == {"sql": "SELECT 1"}
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_execute_api.py -v`
预期：FAIL，404（路由不存在）

- [ ] **步骤 3：实现**

(a) `backend/models/schemas.py` 末尾追加：

```python
class SqlRequest(BaseModel):
    sql: str


class DraftRequest(BaseModel):
    sql: str = ""
```

(b) `backend/routers/execute.py`：

```python
"""POST execute/submit + GET/PUT draft — 页内 SQL 执行与判题"""

from fastapi import APIRouter, HTTPException, Response

from backend.database import get_progress_connection
from backend.grader import grade
from backend.models.schemas import DraftRequest, SqlRequest
from backend.sql_executor import (
    MysqlExecutionError,
    MysqlUnavailableError,
    SqlRejectedError,
    assert_executable,
    execute_statements,
    run_readonly,
    split_statements,
)

MAX_DRAFT_BYTES = 64 * 1024

router = APIRouter()


def _load_problem(problem_id: str):
    conn = get_progress_connection()
    row = conn.execute(
        "SELECT id, db_path, reference_sql, gradable, ordered "
        "FROM problems WHERE id = ?",
        (problem_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Problem not found")
    return row


def _raise_translated(e: Exception):
    if isinstance(e, MysqlUnavailableError):
        raise HTTPException(
            status_code=503,
            detail={"code": "mysql_unavailable", "message": e.message},
        ) from e
    if isinstance(e, SqlRejectedError):
        raise HTTPException(
            status_code=400, detail={"code": e.code, "message": e.message}) from e
    if isinstance(e, MysqlExecutionError):
        raise HTTPException(
            status_code=400,
            detail={"code": f"mysql_{e.mysql_code}", "message": e.message},
        ) from e
    raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/problems/{problem_id}/execute")
def execute_sql(problem_id: str, req: SqlRequest):
    prob = _load_problem(problem_id)
    try:
        return run_readonly(prob["db_path"], req.sql)
    except (SqlRejectedError, MysqlUnavailableError, MysqlExecutionError) as e:
        _raise_translated(e)


@router.post("/problems/{problem_id}/submit")
def submit_sql(problem_id: str, req: SqlRequest):
    prob = _load_problem(problem_id)
    if not prob["gradable"]:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "not_gradable",
                "message": "此题不支持自动判题（DDL/说明题），"
                           "请在 DBeaver 等外部工具完成后手动标记",
            },
        )
    try:
        user_stmts = assert_executable(req.sql)
        ref_stmts = split_statements(prob["reference_sql"])
        user_sets = execute_statements(prob["db_path"], user_stmts)
        ref_sets = execute_statements(prob["db_path"], ref_stmts)
    except (SqlRejectedError, MysqlUnavailableError, MysqlExecutionError) as e:
        _raise_translated(e)
    if not user_sets:
        return {"correct": False, "diffSummary": "查询没有返回结果集"}
    return grade(user_sets[-1], ref_sets, ordered=bool(prob["ordered"]))


@router.get("/problems/{problem_id}/draft")
def get_draft(problem_id: str):
    _load_problem(problem_id)  # 404 校验
    conn = get_progress_connection()
    row = conn.execute(
        "SELECT sql_text FROM drafts WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    conn.close()
    return {"sql": row["sql_text"] if row else ""}


@router.put("/problems/{problem_id}/draft")
def put_draft(problem_id: str, req: DraftRequest):
    _load_problem(problem_id)
    if len(req.sql.encode("utf-8")) > MAX_DRAFT_BYTES:
        raise HTTPException(
            status_code=400,
            detail={"code": "sql_too_large", "message": "草稿超过 64KB 上限"},
        )
    conn = get_progress_connection()
    conn.execute("""
        INSERT OR REPLACE INTO drafts (problem_id, sql_text, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (problem_id, req.sql))
    conn.commit()
    conn.close()
    return Response(status_code=204)
```

(c) `backend/main.py`：import 行与挂载各加一项：

```python
from backend.routers import categories, problems, progress, databases, execute
...
app.include_router(execute.router, prefix="/api")
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_execute_api.py -v`
预期：8 passed

- [ ] **步骤 5：全量回归**

运行：`uv run pytest -v`
预期：全部通过（此前所有测试 + 本任务 8 个）

- [ ] **步骤 6：Commit**

```bash
git add backend/models/schemas.py backend/routers/execute.py backend/main.py tests/backend/test_execute_api.py
git commit -m "feat: execute, submit and draft endpoints for in-app SQL practice"
```

---

### 任务 7：题目详情返回 gradable

**文件：**
- 修改：`backend/routers/problems.py:107-126`（get_problem 响应）
- 修改：`backend/models/schemas.py`（ProblemDetail 补字段）
- 测试：`tests/backend/test_execute_api.py`（追加）

- [ ] **步骤 1：编写失败的测试**

追加到 `tests/backend/test_execute_api.py`：

```python
def test_problem_detail_includes_gradable(client):
    assert client.get("/api/problems/01_01").json()["gradable"] is True
    assert client.get("/api/problems/10_02").json()["gradable"] is False
```

- [ ] **步骤 2：运行测试验证失败**

运行：`uv run pytest tests/backend/test_execute_api.py::test_problem_detail_includes_gradable -v`
预期：FAIL，`KeyError: 'gradable'`

- [ ] **步骤 3：实现**

`backend/routers/problems.py` `get_problem` 返回 dict 中 `"db_file"` 行前追加一行（`SELECT p.*` 已含新列）：

```python
        "gradable": bool(row["gradable"]),
        "db_file": row["db_path"],
```

`backend/models/schemas.py` `ProblemDetail` 的 `db_file` 字段前补：

```python
    gradable: bool = False
```

- [ ] **步骤 4：运行测试验证通过**

运行：`uv run pytest tests/backend/test_execute_api.py -v`
预期：9 passed

- [ ] **步骤 5：Commit**

```bash
git add backend/routers/problems.py backend/models/schemas.py tests/backend/test_execute_api.py
git commit -m "feat: expose gradable flag on problem detail"
```

---

### 任务 8：前端 — 编辑器、执行与判题 UI

**文件：**
- 修改：`frontend/package.json`（依赖）
- 修改：`frontend/src/types.ts`
- 修改：`frontend/src/api.ts`
- 创建：`frontend/src/components/ResultTable.tsx`
- 创建：`frontend/src/components/SQLWorkspace.tsx`
- 修改：`frontend/src/pages/ProblemListPage.tsx`

前端无测试设施（规格约定手动验收），每步以 `npm run build`（含 tsc 类型检查）与浏览器手动验证代替。

- [ ] **步骤 1：安装依赖**

```bash
cd frontend && npm install @uiw/react-codemirror @codemirror/lang-sql
```

- [ ] **步骤 2：types.ts 追加类型**

`frontend/src/types.ts` 末尾追加，并给 `ProblemDetail` 的 `db_file` 前补 `gradable: boolean`：

```typescript
export interface SqlExecuteResult {
  columns: string[]
  rows: unknown[][]
  rowCount: number
  truncated: boolean
  elapsedMs: number
}

export interface SqlSubmitResult {
  correct: boolean
  diffSummary: string | null
}

export interface DraftResponse {
  sql: string
}
```

- [ ] **步骤 3：api.ts 追加函数**

`frontend/src/api.ts` 末尾追加（顶部 import 类型相应补齐 `SqlExecuteResult, SqlSubmitResult, DraftResponse`）：

```typescript
async function postSql<T>(path: string, body: { sql: string }): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let message = `API error ${res.status}`
    try {
      const data = await res.json()
      message = data?.detail?.message ?? data?.detail ?? message
    } catch {
      // 非 JSON 响应体，保留默认 message
    }
    const err = new Error(message) as Error & { status?: number }
    err.status = res.status
    throw err
  }
  return res.json()
}

export function executeSql(id: string, sql: string): Promise<SqlExecuteResult> {
  return postSql(`/problems/${encodeURIComponent(id)}/execute`, { sql })
}

export function submitSql(id: string, sql: string): Promise<SqlSubmitResult> {
  return postSql(`/problems/${encodeURIComponent(id)}/submit`, { sql })
}

export function getDraft(id: string): Promise<DraftResponse> {
  return fetchJson<DraftResponse>(`${BASE}/problems/${encodeURIComponent(id)}/draft`)
}

export async function saveDraft(id: string, sql: string): Promise<void> {
  const res = await fetch(`${BASE}/problems/${encodeURIComponent(id)}/draft`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
}
```

- [ ] **步骤 4：创建 ResultTable 组件**

`frontend/src/components/ResultTable.tsx`：

```typescript
type Col = { name: string; type?: string }

export default function ResultTable({
  columns,
  rows,
}: {
  columns: Col[]
  rows: unknown[][]
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
            {columns.map((col, i) => (
              <th key={i} className="px-4 py-2 font-medium">
                {col.name}
                {col.type && (
                  <span className="ml-1 text-gray-400 font-normal lowercase">{col.type}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t border-gray-100 hover:bg-gray-50">
              {row.map((v, ci) => (
                <td key={ci} className="px-4 py-2 font-mono text-xs text-gray-600">
                  {v === null || v === undefined ? 'NULL' : String(v)}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-4 text-center text-gray-400 text-xs">
                Empty result
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **步骤 5：创建 SQLWorkspace 组件**

`frontend/src/components/SQLWorkspace.tsx`：

```typescript
import { useEffect, useRef, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { sql } from '@codemirror/lang-sql'
import { executeSql, submitSql, getDraft, saveDraft } from '../api'
import type { SqlExecuteResult } from '../types'
import ResultTable from './ResultTable'

type Verdict = { correct: boolean; diffSummary: string | null }

export default function SQLWorkspace({
  problemId,
  gradable,
  onCorrect,
}: {
  problemId: string
  gradable: boolean
  onCorrect: () => void
}) {
  const [code, setCode] = useState('')
  const [result, setResult] = useState<SqlExecuteResult | null>(null)
  const [verdict, setVerdict] = useState<Verdict | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState<'run' | 'submit' | null>(null)
  const debounceRef = useRef<number | null>(null)

  // 切题：回填草稿、清空状态
  useEffect(() => {
    setCode('')
    setResult(null)
    setVerdict(null)
    setError(null)
    getDraft(problemId)
      .then((d) => setCode(d.sql))
      .catch(() => {})
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
  }, [problemId])

  const handleChange = (value: string) => {
    setCode(value)
    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(() => {
      saveDraft(problemId, value).catch(() => {})
    }, 1000)
  }

  const run = async () => {
    setBusy('run')
    try {
      const r = await executeSql(problemId, code)
      setResult(r)
      setVerdict(null)
      setError(null)
      setOffline(false)
    } catch (e) {
      const err = e as Error & { status?: number }
      setOffline(err.status === 503)
      setError(err.status === 503 ? null : err.message)
      setResult(null)
    } finally {
      setBusy(null)
    }
  }

  const submit = async () => {
    setBusy('submit')
    try {
      const v = await submitSql(problemId, code)
      setVerdict(v)
      setError(null)
      setOffline(false)
      if (v.correct) onCorrect()
    } catch (e) {
      const err = e as Error & { status?: number }
      setOffline(err.status === 503)
      setError(err.status === 503 ? null : err.message)
      setVerdict(null)
    } finally {
      setBusy(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (!busy && code.trim()) run()
    }
  }

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Your SQL</h3>

      {offline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-3 mb-3 text-sm">
          MySQL 未启动，请先运行 <code className="font-mono">bash start.sh</code> 后重试
        </div>
      )}

      <div onKeyDown={handleKeyDown} className="border border-gray-200 rounded-lg overflow-hidden">
        <CodeMirror
          value={code}
          onChange={handleChange}
          extensions={[sql()]}
          height="160px"
          theme="light"
          placeholder="-- 在此编写 SQL，Ctrl/⌘ + Enter 运行"
        />
      </div>

      <div className="flex items-center gap-3 mt-3">
        <button
          onClick={run}
          disabled={busy !== null || !code.trim()}
          className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {busy === 'run' ? '运行中…' : '运行'}
        </button>
        {gradable ? (
          <button
            onClick={submit}
            disabled={busy !== null || !code.trim()}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {busy === 'submit' ? '判题中…' : '提交答案'}
          </button>
        ) : (
          <span className="text-xs text-gray-400">
            此题为 DDL/说明题，请在 DBeaver 等外部工具完成后手动标记
          </span>
        )}
        <span className="text-xs text-gray-400">Ctrl/⌘ + Enter 运行</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mt-3 text-sm font-mono whitespace-pre-wrap">
          {error}
        </div>
      )}

      {verdict && (
        <div
          className={`rounded-lg p-3 mt-3 text-sm border ${
            verdict.correct
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          {verdict.correct ? '判定正确！请在弹窗中完成自评' : `判定不符：${verdict.diffSummary}`}
        </div>
      )}

      {result && (
        <div className="mt-3">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <ResultTable
              columns={result.columns.map((c) => ({ name: c }))}
              rows={result.rows}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {result.rowCount} rows · {result.elapsedMs} ms
            {result.truncated ? ' · 超过 500 行，仅展示前 500 行' : ''}
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **步骤 6：集成进 ProblemListPage**

(a) 顶部 import 追加：

```typescript
import SQLWorkspace from '../components/SQLWorkspace'
import ResultTable from '../components/ResultTable'
```

(b) 在 Table Schema 区块（`{tables.length > 0 && (...)}` 结束处，ProblemListPage.tsx:401 的 `)}` 之后、`{/* Reference Answer */}` 之前）插入：

```typescript
            {/* SQL Workspace */}
            <SQLWorkspace
              problemId={detail.id}
              gradable={detail.gradable}
              onCorrect={() => setShowRating(true)}
            />
```

(c) 样例数据表格改用 ResultTable：把 ProblemListPage.tsx:366-397 的 `<div className="overflow-x-auto"><table>...</table></div>` 整块替换为：

```typescript
                    <ResultTable
                      columns={table.columns}
                      rows={table.sample_rows.map((row) =>
                        table.columns.map((c) => row[c.name] ?? null)
                      )}
                    />
```

（外层 `border rounded-lg` 卡片与表头栏保留不动。）

- [ ] **步骤 7：构建与 lint 验证**

```bash
cd frontend && npm run build && npm run lint
```

预期：tsc + vite build 成功退出 0，oxlint 无新增错误。

- [ ] **步骤 8：浏览器手动验证（主工作区跑着服务时在 worktree 验证需临时端口，通常留到合并后统一验收，此处先做构建级验证）**

跳过到任务 9 统一验收亦可。

- [ ] **步骤 9：Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/types.ts frontend/src/api.ts frontend/src/components/ResultTable.tsx frontend/src/components/SQLWorkspace.tsx frontend/src/pages/ProblemListPage.tsx
git commit -m "feat: in-page SQL editor with run, submit and draft autosave"
```

---

### 任务 9：README 更新 + 全量回归 + 手动验收

**文件：**
- 修改：`README.md`
- 修改：`README_zh.md`

- [ ] **步骤 1：更新 README.md**

(a) "Why SQL Dojo?" 对比表（README.md:26）该行改为：

```markdown
| **Practice environment** | Web-based SQL editor | **Built-in editor + your DBeaver for DDL & exploration** |
```

(b) 第 4 节（README.md:86-90）标题与首段替换为：

```markdown
### 4. Practice in the browser (or DBeaver)

Write SQL in the built-in editor on each problem page and click **Run** — queries execute
read-only against the topic schema in Docker MySQL. Click **Submit** to auto-grade your
result against the reference solution (query problems only); a correct answer opens the
mastery self-rating dialog. DDL problems and free exploration still work great in
DBeaver (127.0.0.1:3306, root/practice) — connection info is shown on each problem page.
```

- [ ] **步骤 2：更新 README_zh.md 同位置（README_zh.md:26、86-90）**

```markdown
| **练习环境** | 网页 SQL 编辑器 | **内置编辑器 + DBeaver（DDL 与自由探索）** |
```

```markdown
### 4. 在浏览器中练习（或 DBeaver）

在题目页内置编辑器中写 SQL，点「运行」——查询以只读方式在 Docker MySQL 的专题 schema 上执行。
点「提交答案」自动与参考答案比对判题（仅查询题）；判对后弹出掌握度自评弹窗。
DDL 题与自由探索仍推荐 DBeaver（127.0.0.1:3306，root/practice），题目页有连接信息可一键复制。
```

- [ ] **步骤 3：全量回归**

```bash
uv run pytest -v
uv run python data_builder/smoke_test.py
```

预期：pytest 全部通过；smoke 输出无 ✗、失败为"无"。

- [ ] **步骤 4：真实 progress.db 迁移（一次性）**

```bash
uv run python -c "from backend.database import init_progress_db, seed_problems; init_progress_db(); seed_problems()"
```

预期：无输出正常退出（老库被幂等加上 gradable/ordered 列并重播 gradable 标记）。

- [ ] **步骤 5：手动验收（合并回主分支并 `bash start.sh` 后执行）**

逐项核对规格验收标准：

1. 打开查询题（如 01-01），编辑器输入 SQL 点「运行」，出现结果表格与「N rows · M ms」
2. 输入 `DELETE FROM test` 点运行 → 红色错误提示「只允许查询语句…」
3. 用参考答案本身提交 → 绿色「判定正确」+ 弹出自评弹窗，提交后左侧列表状态变 completed
4. 写一个 `SELECT 1 AS one` 提交 → 红色「判定不符：列数不符…」
5. 刷新页面重进该题 → 编辑器回填上次草稿
6. 打开 10-02（DDL 题）→ 有「运行」无「提交答案」，显示外部工具提示
7. `docker compose stop mysql` 后点运行 → 黄色「MySQL 未启动」提示；`docker compose start mysql` 恢复后可执行

- [ ] **步骤 6：Commit**

```bash
git add README.md README_zh.md
git commit -m "docs: in-page SQL execution as primary practice flow"
```

---

## 自检记录

- **规格覆盖度：** 三层只读防护（任务 2 白名单、任务 3 READ ONLY + 超时）、拆句与最后结果集（任务 2/3）、行数上限 500 与 64KB（任务 2/3）、判题语义含归一化/顺序开关/差异摘要（任务 4）、gradable 标记与幂等迁移（任务 5）、API 契约四端点与错误码转译（任务 3/6）、detail gradable（任务 7）、前端编辑器/双按钮/结果表/反馈横幅/草稿 debounce/离线提示/防重（任务 8）、README（任务 9）、测试策略（任务 1-7 pytest + 任务 9 回归与验收清单）——均有对应任务。
- **占位符扫描：** 无"待定/TODO/类似任务 N"；所有代码步骤含完整代码。
- **类型一致性：** `SqlRejectedError(code, message)` / `MysqlUnavailableError(message)` / `MysqlExecutionError(mysql_code, message)` 在任务 2 定义、任务 3/6 使用一致；`execute_statements(schema, stmts, timeout_ms)` 结果集结构 `{"columns","rows","truncated"}` 与任务 4 `grade(user, reference_sets, ordered)` 入参一致；`run_readonly` 返回五字段与前端 `SqlExecuteResult` 一致；`problems.gradable/ordered` 在任务 5 写入、任务 6/7 读取；前端 `detail.gradable` 由任务 7 后端字段供给。
