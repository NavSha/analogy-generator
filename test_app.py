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
        "metadatas": [
            {"concept": "Recursion", "analogy": "Recursion is like..."},
            {"concept": "API (Application Programming Interface)", "analogy": "An API is like..."},
            {"concept": "Recursion", "analogy": "Recursion is also like..."},
        ]
    }
    col.query.return_value = {
        "ids": [["recursion-everyday-001"]],
        "metadatas": [[{"concept": "Recursion", "analogy": "Recursion is like standing between two mirrors."}]],
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
