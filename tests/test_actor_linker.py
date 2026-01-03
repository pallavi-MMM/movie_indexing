from src.actor_linker import ActorLinker


def test_mock_actor_matching():
    al = ActorLinker(mode="mock")
    al.add_actor("Alice", [1.0, 0.0, 0.0])
    al.add_actor("Bob", [0.0, 1.0, 0.0])
    res = al.match_embedding([0.9, 0.1, 0.0], threshold=0.5)
    assert res["matched"] is True
    assert res["name"] == "Alice"
    assert res["confidence"] > 0.5


def test_unknown_when_below_threshold():
    al = ActorLinker(mode="mock")
    al.add_actor("Alice", [1.0, 0.0, 0.0])
    res = al.match_embedding([0.0, 0.0, 1.0], threshold=0.5)
    assert res["matched"] is False
    assert res["name"] == "unknown"
