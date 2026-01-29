from src.scene_fusion import merge_scenes_from_sources


def _make_source(scene, name):
    return {"scene": scene, "source": name}


def test_merge_scalar_prefers_higher_confidence():
    a = _make_source(
        {
            "scene_id": "s1",
            "scene_summary": "alpha",
            "field_confidences": {"scene_summary": 0.6},
        },
        "phase_a",
    )
    b = _make_source(
        {
            "scene_id": "s1",
            "scene_summary": "beta",
            "field_confidences": {"scene_summary": 0.9},
        },
        "phase_b",
    )
    m = merge_scenes_from_sources([a, b])
    assert m["scene_summary"] == "beta"
    assert m["field_confidences"]["scene_summary"] == 0.9
    assert (
        "phase_a" in m["field_provenance"]["scene_summary"]
        and "phase_b" in m["field_provenance"]["scene_summary"]
    )


def test_merge_array_union_and_confidence():
    a = _make_source(
        {"objects": [{"type": "car"}], "field_confidences": {"objects": 0.6}}, "obj_a"
    )
    b = _make_source(
        {
            "objects": [{"type": "person"}, {"type": "car"}],
            "field_confidences": {"objects": 0.85},
        },
        "obj_b",
    )
    m = merge_scenes_from_sources([a, b])
    objs = m["objects"]
    assert any(o.get("type") == "car" for o in objs)
    assert any(o.get("type") == "person" for o in objs)
    assert m["field_confidences"]["objects"] == 0.85


def test_missing_confidences_defaults_and_provenance():
    a = _make_source({"dialogue_text": [{"line": "hello"}]}, "d_a")
    b = _make_source({"dialogue_text": [{"line": "hello"}]}, "d_b")
    m = merge_scenes_from_sources([a, b])
    assert m["dialogue_text"] == [{"line": "hello"}]
    # no field_confidences key when none provided
    assert (
        "field_confidences" not in m
        or m["field_confidences"].get("dialogue_text") is None
    )
    assert "field_provenance" in m and "d_a" in m["field_provenance"]["dialogue_text"]
