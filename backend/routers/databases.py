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
