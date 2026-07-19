"""Pydantic models for API request/response"""

from pydantic import BaseModel
from typing import List, Optional


class ProgressInfo(BaseModel):
    status: str = "not_started"
    completed_count: int = 0
    mastery_level: int = 0
    last_practiced_at: Optional[str] = None


class ProblemBrief(BaseModel):
    id: str
    title: str
    difficulty: int
    tags: List[str] = []
    progress: Optional[ProgressInfo] = None


class CategoryInfo(BaseModel):
    id: str
    name: str
    db_file: str
    order: int
    stats: dict  # {total, completed, avg_mastery}


class CategoryListResponse(BaseModel):
    categories: List[CategoryInfo]
    global_stats: dict


class ProblemListResponse(BaseModel):
    category: CategoryInfo
    problems: List[ProblemBrief]
    stats: dict


class ProblemDetail(BaseModel):
    id: str
    category_id: str
    title: str
    difficulty: int
    tags: List[str]
    description: str
    reference_sql: str
    tables: List[str]
    hints: List[str]
    progress: Optional[ProgressInfo]
    db_file: str
    db_connection: str  # DBeaver connection string


class TableInfo(BaseModel):
    name: str
    columns: List[dict]
    row_count: int
    sample_rows: List[dict]


class TablesResponse(BaseModel):
    tables: List[TableInfo]
    db_connection: str


class CompleteRequest(BaseModel):
    action: str = "complete"  # always "complete"
    mastery: int = 3  # 1-5


class ProgressUpdate(BaseModel):
    mastery_level: Optional[int] = None
    notes: Optional[str] = None


class ProgressSummary(BaseModel):
    total: int
    completed: int
    in_progress: int
    not_started: int
    avg_mastery: float


class DbConnectionResponse(BaseModel):
    db_file: str
    connection_string: str
