from src.scene_fusion import merge_scenes_from_sources


def test_merge_characters_aggregates_screen_time_and_confidence():
    s1 = {
        "scene": {
            "scene_id": "s1",
            "characters": [{"name": "Alice", "screen_time": 5.0}],
            "field_confidences": {"characters": 0.9},
            "field_provenance": {"characters": ["face_tracker_v1"]},
        },
        "source": "face_tracker_v1",
    }
    s2 = {
        "scene": {
            "scene_id": "s1",
            "characters": [{"name": "Alice", "screen_time": 3.0}, {"name": "Bob", "screen_time": 2.0}],
            "field_confidences": {"characters": 0.8},
            "field_provenance": {"characters": ["face_tracker_v2"]},
        },
        "source": "face_tracker_v2",
    }
    merged = merge_scenes_from_sources([s1, s2])
    assert "characters" in merged
    chars = {c["name"]: c for c in merged["characters"]}
    assert "Alice" in chars and "Bob" in chars
    assert abs(chars["Alice"]["screen_time"] - 8.0) < 1e-6
    assert abs(chars["Bob"]["screen_time"] - 2.0) < 1e-6
    # Check per-character confidences mapped in field_confidences
    assert "field_confidences" in merged and isinstance(merged["field_confidences"], dict)
    confs = merged["field_confidences"]["characters"]
    assert confs.get("Alice") == 0.9
    assert confs.get("Bob") == 0.8
    # provenance union
    provs = merged.get("field_provenance", {}).get("characters", [])
    assert "face_tracker_v1" in provs and "face_tracker_v2" in provs
