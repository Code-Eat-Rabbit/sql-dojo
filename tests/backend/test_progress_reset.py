"""进度一键重置：清 progress、保留 drafts、problems 不动"""


def test_reset_clears_progress_keeps_drafts(client):
    # 造状态：完成两题 + 写一条草稿
    assert client.post(
        "/api/progress/01_01", json={"action": "complete", "mastery": 4}
    ).status_code == 200
    assert client.post(
        "/api/progress/01_02", json={"action": "complete", "mastery": 3}
    ).status_code == 200
    assert client.put(
        "/api/problems/01_01/draft", json={"sql": "SELECT 1"}
    ).status_code == 204

    r = client.post("/api/progress/reset")
    assert r.status_code == 200
    assert r.json() == {"reset": True, "cleared": 44}

    # 进度归零（summary 无副作用，先于 detail 调用）
    summary = client.get("/api/progress/summary").json()
    assert summary["completed"] == 0
    assert summary["in_progress"] == 0
    assert summary["not_started"] == summary["total"]

    # 草稿保留
    assert client.get("/api/problems/01_01/draft").json() == {"sql": "SELECT 1"}

    # problems 表行数不变（种子数据不受重置影响）
    import sqlite3
    from backend.database import get_progress_connection

    conn = get_progress_connection()
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM problems").fetchone()["n"]
    finally:
        conn.close()
    assert n == 44
