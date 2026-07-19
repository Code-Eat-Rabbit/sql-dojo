"""GET /api/databases/{id}/connect"""

from fastapi import APIRouter
from backend.database import get_practice_db_path

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

    db_path = get_practice_db_path(cat.db_file)
    return {
        "db_file": cat.db_file,
        "connection_string": f"sqlite:///{db_path}",
        "exists": db_path.exists(),
    }
