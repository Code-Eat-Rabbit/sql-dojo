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
