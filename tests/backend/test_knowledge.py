"""knowledge 字段：API 透传（内容在任务 3 填充）"""


def test_problem_list_category_contains_knowledge(client):
    r = client.get("/api/problems?category_id=01")
    assert r.status_code == 200
    cat = r.json()["category"]
    assert "knowledge" in cat
    assert isinstance(cat["knowledge"], str)


def test_categories_contain_knowledge(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    cats = r.json()["categories"]
    assert len(cats) == 14
    for c in cats:
        assert "knowledge" in c
        assert isinstance(c["knowledge"], str)


def test_all_categories_have_knowledge_content(client):
    cats = client.get("/api/categories").json()["categories"]
    for c in cats:
        assert "## 解题思路" in c["knowledge"], f"category {c['id']} 缺解题思路"
        assert "## 必背知识点" in c["knowledge"], f"category {c['id']} 缺必背知识点"
