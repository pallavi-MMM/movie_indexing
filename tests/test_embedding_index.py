from src.embedding_index import EmbeddingIndex


def test_add_and_query_basic():
    idx = EmbeddingIndex(dim=3)
    idx.add("s1", [1.0, 0.0, 0.0], {"movie_id": "m1"})
    idx.add("s2", [0.0, 1.0, 0.0], {"movie_id": "m1"})
    idx.add("s3", [0.9, 0.1, 0.0], {"movie_id": "m2"})
    assert idx.size() == 3

    # Query near s1
    res = idx.query([1.0, 0.0, 0.0], top_k=2)
    assert len(res) == 2
    assert res[0][0] == "s1"
    # s3 should come second because it's similar to s1
    assert res[1][0] == "s3"


def test_dimension_mismatch_raises():
    idx = EmbeddingIndex(dim=4)
    try:
        idx.add("s1", [1.0, 0.0, 0.0])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
