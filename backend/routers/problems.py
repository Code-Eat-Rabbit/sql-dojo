"""GET /api/problems -- problem list + detail + table schemas"""

import json
from fastapi import APIRouter, HTTPException, Query
from backend.database import (
    get_progress_connection, get_practice_db_path, get_table_schema
)

router = APIRouter()


@router.get("/problems")
def list_problems(category_id: str = Query(None)):
    """Get problem list, optionally filtered by category"""
    conn = get_progress_connection()

    where = "WHERE p.category_id = ?" if category_id else ""
    params = (category_id,) if category_id else ()

    rows = conn.execute(f"""
        SELECT p.*, pr.status, pr.completed_count, pr.mastery_level,
               pr.last_practiced_at
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        {where}
        ORDER BY p.id
    """, params).fetchall()

    problems = []
    for r in rows:
        problems.append({
            "id": r["id"],
            "category_id": r["category_id"],
            "title": r["title"],
            "difficulty": r["difficulty"],
            "tags": json.loads(r["tags"]) if r["tags"] else [],
            "progress": {
                "status": r["status"] or "not_started",
                "completed_count": r["completed_count"] or 0,
                "mastery_level": r["mastery_level"] or 0,
                "last_practiced_at": r["last_practiced_at"],
            }
        })

    # Stats
    stats = conn.execute(f"""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN pr.status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        {where}
    """, params).fetchone()

    # Category info
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import get_category

    cat = get_category(category_id) if category_id else None

    conn.close()

    return {
        "category": {
            "id": cat.id if cat else "",
            "name": cat.name if cat else "",
            "db_file": cat.db_file if cat else "",
            "order": cat.order if cat else 0,
        } if cat else None,
        "problems": problems,
        "stats": {
            "total": stats["total"],
            "completed": stats["completed"] or 0,
        }
    }


@router.get("/problems/{problem_id}")
def get_problem(problem_id: str):
    """Get single problem detail"""
    conn = get_progress_connection()

    row = conn.execute("""
        SELECT p.*, pr.status, pr.completed_count, pr.mastery_level,
               pr.last_practiced_at, pr.notes
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        WHERE p.id = ?
    """, (problem_id,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    # Mark as in_progress on first view
    if row["status"] == "not_started":
        conn.execute("""
            UPDATE progress SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP
            WHERE problem_id = ?
        """, (problem_id,))
        conn.commit()

    conn.close()

    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "title": row["title"],
        "difficulty": row["difficulty"],
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "description": row["description"] or "",
        "reference_sql": row["reference_sql"] or "",
        "tables": json.loads(row["table_names"]) if row["table_names"] else [],
        "hints": json.loads(row["hints"]) if row["hints"] else [],
        "progress": {
            "status": row["status"] or "not_started",
            "completed_count": row["completed_count"] or 0,
            "mastery_level": row["mastery_level"] or 0,
            "last_practiced_at": row["last_practiced_at"],
        },
        "db_file": row["db_path"].split("/")[-1] if row["db_path"] else "",
        "db_connection": f"sqlite:///{row['db_path']}",
    }


@router.get("/problems/{problem_id}/tables")
def get_problem_tables(problem_id: str):
    """Get table schemas and sample data for a problem"""
    conn = get_progress_connection()

    row = conn.execute(
        "SELECT db_path, table_names FROM problems WHERE id = ?",
        (problem_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    db_file = row["db_path"].split("/")[-1] if row["db_path"] else ""
    table_names = json.loads(row["table_names"]) if row["table_names"] else []

    tables = []
    for tname in table_names:
        info = get_table_schema(db_file, tname)
        if info:
            tables.append(info)

    conn.close()

    return {
        "tables": tables,
        "db_connection": f"sqlite:///{row['db_path']}",
    }
