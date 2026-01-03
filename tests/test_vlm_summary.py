from src.vlm_summary import summarize_scene


def test_summarize_from_dialogue_and_characters():
    scene = {
        "scene_id": "s1",
        "movie_id": "m1",
        "dialogue_text": [{"character": "Alice", "line": "We must leave now."}, {"character": "Bob", "line": "No, stay."}],
        "characters": [{"name": "Alice"}, {"name": "Bob"}],
    }
    out = summarize_scene(scene)
    assert "Dialogue:" in out["scene_summary"]
    assert "Characters:" in out["scene_summary"]
    assert "Alice" in out["keywords_auto_generated"]
    assert "scene_summary" in out and isinstance(out["scene_summary"], str)


def test_includes_visual_and_safety_notes_if_present():
    scene = {
        "scene_id": "s2",
        "movie_id": "m1",
        "quality_flags": {"black_frames_detected": True},
        "safety_flags": {"violence": True},
    }
    out = summarize_scene(scene)
    assert "black frames" in out["scene_summary"].lower()
    assert "violent" in out["scene_summary"].lower()
    assert out["field_confidences"].get("scene_summary.safety") is not None


def test_fallback_when_nothing_present():
    scene = {"scene_id": "s3", "movie_id": "m1"}
    out = summarize_scene(scene)
    assert out["scene_summary"].startswith("No salient dialogue")
    assert out["field_confidences"]["scene_summary.fallback"] == 0.2
