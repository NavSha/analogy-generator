import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def mock_collection():
    col = MagicMock()
    col.count.return_value = 228
    col.get.return_value = {
        "ids": ["rec-001", "api-001", "rec-002"],
        "metadatas": [
            {"concept": "Recursion", "analogy": "Recursion is like...", "category": "Programming Concepts"},
            {"concept": "API (Application Programming Interface)", "analogy": "An API is like...", "category": "Web Fundamentals"},
            {"concept": "Recursion", "analogy": "Recursion is also like...", "category": "Programming Concepts"},
        ]
    }
    col.query.return_value = {
        "ids": [["recursion-everyday-001"]],
        "metadatas": [[{"concept": "Recursion", "analogy": "Recursion is like standing between two mirrors.", "category": "Programming Concepts"}]],
        "distances": [[0.25]],
    }
    return col


# ── Route tests ──


def test_index_returns_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"Analogy Generator" in res.data


@patch("app.get_collection")
def test_concepts_returns_sorted_list(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.get("/concepts")
    assert res.status_code == 200
    data = res.get_json()
    assert data == ["API (Application Programming Interface)", "Recursion"]


@patch("app.get_collection")
def test_concepts_empty_when_no_collection(mock_get, client):
    mock_get.return_value = None
    res = client.get("/concepts")
    assert res.status_code == 200
    assert res.get_json() == []


@patch("app.get_collection")
def test_search_valid_concept(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.post("/search", json={"concept": "recursion"})
    assert res.status_code == 200
    data = res.get_json()
    assert "results" in data
    assert len(data["results"]) == 1
    result = data["results"][0]
    assert "id" in result
    assert "concept" in result
    assert "analogy" in result
    assert "distance" in result


@patch("app.get_collection")
def test_search_empty_concept_returns_400(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.post("/search", json={"concept": ""})
    assert res.status_code == 400
    assert "error" in res.get_json()


@patch("app.get_collection")
def test_search_whitespace_only_returns_400(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.post("/search", json={"concept": "   "})
    assert res.status_code == 400


@patch("app.get_collection")
def test_search_no_collection_returns_503(mock_get, client):
    mock_get.return_value = None
    res = client.post("/search", json={"concept": "recursion"})
    assert res.status_code == 503
    assert "error" in res.get_json()


@patch("app.get_collection")
def test_search_exclude_ids(mock_get, client):
    col = MagicMock()
    col.count.return_value = 2
    col.query.return_value = {
        "ids": [["id-excluded", "id-kept"]],
        "metadatas": [[
            {"concept": "Cache", "analogy": "Excluded analogy"},
            {"concept": "Cache", "analogy": "Kept analogy"},
        ]],
        "distances": [[0.2, 0.3]],
    }
    mock_get.return_value = col

    res = client.post("/search", json={
        "concept": "cache",
        "exclude_ids": ["id-excluded"],
    })
    assert res.status_code == 200
    data = res.get_json()
    ids = [r["id"] for r in data["results"]]
    assert "id-excluded" not in ids
    assert "id-kept" in ids


@patch("app.get_collection")
def test_search_n_results_capped_at_20(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    client.post("/search", json={"concept": "recursion", "n_results": 100})
    # Verify query was called with n_results capped (20 + 0 exclude_ids = 20)
    call_args = mock_collection.query.call_args
    assert call_args.kwargs.get("n_results", call_args[1].get("n_results")) <= 20


@patch("app.get_collection")
def test_search_deduplicates_analogies(mock_get, client):
    col = MagicMock()
    col.count.return_value = 3
    col.query.return_value = {
        "ids": [["id1", "id2"]],
        "metadatas": [[
            {"concept": "DNS", "analogy": "DNS is like a phone book."},
            {"concept": "DNS", "analogy": "DNS is like a phone book."},
        ]],
        "distances": [[0.1, 0.15]],
    }
    mock_get.return_value = col

    res = client.post("/search", json={"concept": "DNS"})
    data = res.get_json()
    assert len(data["results"]) == 1


# ── Edge cases ──


@patch("app.get_collection")
def test_search_no_results(mock_get, client):
    col = MagicMock()
    col.count.return_value = 1
    col.query.return_value = {"ids": [[]], "metadatas": [[]], "distances": [[]]}
    mock_get.return_value = col

    res = client.post("/search", json={"concept": "xyznonexistent"})
    assert res.status_code == 200
    assert res.get_json()["results"] == []


@patch("app.get_collection")
def test_search_chromadb_exception_returns_500(mock_get, client):
    col = MagicMock()
    col.count.return_value = 1
    col.query.side_effect = Exception("ChromaDB internal error")
    mock_get.return_value = col

    res = client.post("/search", json={"concept": "recursion"})
    assert res.status_code == 500
    assert "error" in res.get_json()
    # Should NOT leak internal exception details
    assert "ChromaDB internal error" not in res.get_json()["error"]


# ── New feature tests ──


@patch("app.get_collection")
def test_categories_returns_list(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.get("/categories")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "count" in data[0]


@patch("app.get_collection")
def test_concepts_filtered_by_category(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.get("/concepts?category=Programming Concepts")
    assert res.status_code == 200
    data = res.get_json()
    assert "Recursion" in data
    assert "API (Application Programming Interface)" not in data


@patch("app.get_collection")
def test_daily_returns_analogy(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.get("/daily")
    assert res.status_code == 200
    data = res.get_json()
    assert "id" in data
    assert "concept" in data
    assert "analogy" in data
    assert "category" in data


@patch("app.get_collection")
def test_daily_deterministic(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res1 = client.get("/daily")
    res2 = client.get("/daily")
    assert res1.get_json() == res2.get_json()


@patch("app.get_collection")
def test_daily_no_collection_returns_503(mock_get, client):
    mock_get.return_value = None
    res = client.get("/daily")
    assert res.status_code == 503


def test_analytics_empty_initially(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.ANALYTICS_FILE", str(tmp_path / "analytics.json"))
    res = client.get("/analytics")
    assert res.status_code == 200
    assert res.get_json() == {"top_concepts": []}


@patch("app.get_collection")
def test_search_logs_analytics(mock_get, client, mock_collection, tmp_path, monkeypatch):
    analytics_file = str(tmp_path / "analytics.json")
    monkeypatch.setattr("app.ANALYTICS_FILE", analytics_file)
    mock_get.return_value = mock_collection
    client.post("/search", json={"concept": "recursion"})
    import json as json_lib
    with open(analytics_file) as f:
        entries = json_lib.load(f)
    assert len(entries) == 1
    assert entries[0]["query"] == "recursion"


@patch("app.get_collection")
def test_search_result_includes_category(mock_get, client, mock_collection):
    mock_get.return_value = mock_collection
    res = client.post("/search", json={"concept": "recursion"})
    assert res.status_code == 200
    data = res.get_json()
    assert "category" in data["results"][0]
