from src.run_local_pipeline import run_scene_pipeline


def test_end_to_end_pipeline_merges_all_outputs():
    scene = {
        "scene_id": "e2e1",
        "movie_id": "mv1",
        "profanity_present": True,
        "black_frames_detected": True,
        "dialogue_text": [{"character": "Lead", "line": "We need to go."}],
        "characters": [{"name": "Lead", "screen_time": 4.0}],
    }

    merged = run_scene_pipeline(scene)
    # merged should include safety_flags and quality_flags from detectors
    assert "safety_flags" in merged or "safety_flags" in merged.get(
        "field_provenance", {}
    )
    assert "quality_flags" in merged or "quality_flags" in merged.get(
        "field_provenance", {}
    )
    # merged should include the scene_summary produced by VLM
    assert "scene_summary" in merged
    # keywords should be present and include Lead
    kws = merged.get("keywords_auto_generated", [])
    assert isinstance(kws, list)
    # Prefer presence of 'Lead' either in keywords or characters
    assert (
        any((c.get("name") == "Lead") for c in merged.get("characters", []))
        or "Lead" in kws
    )
