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
