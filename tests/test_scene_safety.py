from src.scene_safety import analyze_scene


def test_detects_profanity_from_field():
    scene = {"scene_id": "s1", "movie_id": "m1", "profanity_present": True}
    out = analyze_scene(scene)
    assert out["safety_flags"]["strong_language"] is True
    assert out["field_confidences"]["strong_language"] >= 0.9
    assert "dialogue_profanity_detector" in out["field_provenance"]["strong_language"]


def test_detects_violence_level_string():
    scene = {"scene_id": "s2", "movie_id": "m1", "violence_level": "High and graphic"}
    out = analyze_scene(scene)
    assert out["safety_flags"]["violence"] is True
    assert out["field_confidences"]["violence"] >= 0.9


def test_defaults_low_confidence_when_absent():
    scene = {"scene_id": "s3", "movie_id": "m1"}
    out = analyze_scene(scene)
    # No explicit signals -> low-confidence false flags
    assert out["safety_flags"]["violence"] is False
    assert out["field_confidences"]["violence"] == 0.1
