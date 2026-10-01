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
