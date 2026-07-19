"""FastAPI application entry point"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import categories, problems, progress, databases

app = FastAPI(title="SQL Practice Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix="/api")
app.include_router(problems.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(databases.router, prefix="/api")


@app.get("/api/health")
def health():
    from backend.database import DATABASES_DIR
    return {
        "status": "ok",
        "databases_dir": str(DATABASES_DIR),
    }
