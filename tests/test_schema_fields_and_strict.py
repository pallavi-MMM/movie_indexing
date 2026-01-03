import os
import importlib

from src.scene_schema import validate_scene, enforce_scene


def test_character_dominance_ranking_valid():
    scene = {
        "scene_id": "s1",
        "movie_id": "M",
        "character_dominance_ranking": [
            {"character": "Alice", "score": 0.8},
            {"character": "Bob", "score": 0.2},
        ],
    }

    valid, msgs = validate_scene(scene)
    assert valid, f"Expected valid scene, got messages: {msgs}"


def test_character_dominance_ranking_invalid_score():
    scene = {"scene_id": "s2", "movie_id": "M", "character_dominance_ranking": [{"character": "X", "score": 1.5}]}
    valid, msgs = validate_scene(scene)
    assert not valid
    assert any("character_dominance_ranking" in m or "score" in m or "invalid" in m for m in msgs)


def test_field_confidences_structure():
    scene = {"scene_id": "s3", "movie_id": "M", "field_confidences": {"dialogue_text": 0.92, "objects": 0.6}}
    valid, msgs = validate_scene(scene)
    assert valid

    scene_bad = {"scene_id": "s3", "movie_id": "M", "field_confidences": {"dialogue_text": "high"}}
    valid, msgs = validate_scene(scene_bad)
    assert not valid
    assert any("field_confidences" in m or "dialogue_text" in m or "invalid" in m for m in msgs)


def test_enforce_scene_strict_mode_raises(monkeypatch):
    # Reload module with SCHEMA_STRICT enabled to test enforce behavior
    monkeypatch.setenv("SCHEMA_STRICT", "1")
    import src.scene_schema as ss
    importlib.reload(ss)

    bad_scene = {"movie_id": "no_scene_id"}  # missing scene_id
    try:
        # enforce_scene should raise a RuntimeError in strict mode
        try:
            ss.enforce_scene(bad_scene)
            raised = False
        except RuntimeError:
            raised = True
        assert raised
    finally:
        # Unset strict and reload to avoid impacting other tests
        monkeypatch.delenv("SCHEMA_STRICT", raising=False)
        importlib.reload(ss)
