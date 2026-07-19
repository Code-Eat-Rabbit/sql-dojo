"""GET /api/categories -- category list with progress stats"""

import json
from fastapi import APIRouter
from backend.database import get_progress_connection

router = APIRouter()


@router.get("/categories")
def list_categories():
    conn = get_progress_connection()

    rows = conn.execute("""
        SELECT p.category_id, p.title, COUNT(*) as total,
               SUM(CASE WHEN pr.status = 'completed' THEN 1 ELSE 0 END) as completed,
               ROUND(AVG(pr.mastery_level), 1) as avg_mastery
        FROM problems p
        LEFT JOIN progress pr ON p.id = pr.problem_id
        GROUP BY p.category_id
        ORDER BY p.category_id
    """).fetchall()

    categories = []
    total_problems = 0
    total_completed = 0
    total_mastery_sum = 0.0

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from data_builder.manifest import CATEGORIES

    cat_map = {c.id: c for c in CATEGORIES}

    for row in rows:
        cat = cat_map.get(row["category_id"])
        categories.append({
            "id": row["category_id"],
            "name": cat.name if cat else row["category_id"],
            "db_file": cat.db_file if cat else "",
            "order": cat.order if cat else 99,
            "stats": {
                "total": row["total"],
                "completed": row["completed"],
                "avg_mastery": row["avg_mastery"] or 0,
            }
        })
        total_problems += row["total"]
        total_completed += row["completed"]
        total_mastery_sum += (row["avg_mastery"] or 0) * row["total"]

    conn.close()

    return {
        "categories": sorted(categories, key=lambda c: c["order"]),
        "global_stats": {
            "total": total_problems,
            "completed": total_completed,
            "avg_mastery": round(total_mastery_sum / total_problems, 1) if total_problems else 0,
        }
    }
