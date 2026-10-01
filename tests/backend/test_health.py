"""TestClient 冒烟：应用可导入、health 端点可用"""


def test_health():
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
