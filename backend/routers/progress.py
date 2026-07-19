"""POST/PATCH/GET /api/progress -- progress management"""

import json
from fastapi import APIRouter, HTTPException
from backend.database import get_progress_connection
from backend.models.schemas import CompleteRequest, ProgressUpdate

router = APIRouter()


def compute_mastery(completed_count: int, manual_level: int,
                    last_practiced_at: str | None) -> int:
    """Calculate mastery: MAX(manual, auto) + time decay"""
    # Auto rating
    if completed_count >= 5:
        auto = 5
    elif completed_count >= 3:
        auto = 3
    elif completed_count >= 1:
        auto = 2
    else:
        auto = 0

    result = max(manual_level, auto)

    # Time decay: drop one level after 30 days
    if last_practiced_at:
        from datetime import datetime, timedelta
        try:
            last = datetime.fromisoformat(last_practiced_at)
            if (datetime.now() - last) > timedelta(days=30):
                result = max(1, result - 1)
        except ValueError:
            pass

    return result


@router.post("/progress/{problem_id}")
def complete_problem(problem_id: str, req: CompleteRequest):
    """Mark a problem as completed"""
    conn = get_progress_connection()

    # Verify problem exists
    prob = conn.execute(
        "SELECT id FROM problems WHERE id = ?", (problem_id,)
    ).fetchone()
    if not prob:
        conn.close()
        raise HTTPException(status_code=404, detail="Problem not found")

    # Get current progress
    cur = conn.execute(
        "SELECT completed_count, mastery_level FROM progress WHERE problem_id = ?",
        (problem_id,)
    ).fetchone()

    new_count = (cur["completed_count"] or 0) + 1
    new_mastery = compute_mastery(new_count, req.mastery, None)

    conn.execute("""
        UPDATE progress
        SET status = 'completed',
            completed_count = ?,
            mastery_level = ?,
            last_practiced_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE problem_id = ?
    """, (new_count, new_mastery, problem_id))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM progress WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    conn.close()

    return {
        "problem_id": problem_id,
        "status": row["status"],
        "completed_count": row["completed_count"],
        "mastery_level": row["mastery_level"],
        "last_practiced_at": row["last_practiced_at"],
    }


@router.patch("/progress/{problem_id}")
def update_progress(problem_id: str, req: ProgressUpdate):
    """Update mastery level or notes"""
    conn = get_progress_connection()

    cur = conn.execute(
        "SELECT completed_count, mastery_level, last_practiced_at FROM progress WHERE problem_id = ?",
        (problem_id,)
    ).fetchone()

    if not cur:
        conn.close()
        raise HTTPException(status_code=404, detail="Progress not found")

    manual = req.mastery_level if req.mastery_level is not None else (cur["mastery_level"] or 0)
    new_mastery = compute_mastery(
        cur["completed_count"] or 0,
        manual,
        cur["last_practiced_at"]
    )

    if req.notes is not None:
        conn.execute(
            "UPDATE progress SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE problem_id = ?",
            (req.notes, problem_id)
        )

    conn.execute("""
        UPDATE progress
        SET mastery_level = ?, updated_at = CURRENT_TIMESTAMP
        WHERE problem_id = ?
    """, (new_mastery, problem_id))
    conn.commit()

    row = conn.execute(
        "SELECT * FROM progress WHERE problem_id = ?", (problem_id,)
    ).fetchone()
    conn.close()

    return {
        "problem_id": problem_id,
        "mastery_level": row["mastery_level"],
        "notes": row["notes"],
    }


@router.get("/progress/summary")
def progress_summary():
    """Global progress statistics"""
    conn = get_progress_connection()

    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started,
            ROUND(AVG(mastery_level), 1) as avg_mastery
        FROM progress
    """).fetchone()

    conn.close()

    return {
        "total": row["total"],
        "completed": row["completed"] or 0,
        "in_progress": row["in_progress"] or 0,
        "not_started": row["not_started"] or 0,
        "avg_mastery": row["avg_mastery"] or 0,
    }
