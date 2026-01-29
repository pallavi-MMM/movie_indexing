from src.scene_fusion import merge_scenes_from_sources


def test_merge_vlm_scene_summary_and_keywords():
    s1 = {
        "scene": {
            "scene_id": "s_v1",
            "movie_id": "m1",
            "scene_summary": "A tense exchange at dusk.",
            "keywords_auto_generated": ["tense", "exchange"],
            "field_confidences": {"scene_summary": 0.8, "keywords_auto_generated": 0.8},
            "field_provenance": {
                "scene_summary": ["vlm_v1"],
                "keywords_auto_generated": ["vlm_v1"],
            },
        },
        "source": "vlm_v1",
    }

    s2 = {
        "scene": {
            "scene_id": "s_v1",
            "movie_id": "m1",
            "scene_summary": "A heated argument between two characters.",
            "keywords_auto_generated": ["argument", "characters"],
            "field_confidences": {
                "scene_summary": 0.92,
                "keywords_auto_generated": 0.85,
            },
            "field_provenance": {
                "scene_summary": ["vlm_v2"],
                "keywords_auto_generated": ["vlm_v2"],
            },
        },
        "source": "vlm_v2",
    }

    merged = merge_scenes_from_sources([s1, s2])
    # scene_summary should be chosen from s2 (higher confidence)
    assert merged.get("scene_summary") == s2["scene"]["scene_summary"]
    # keywords should be unioned
    kws = merged.get("keywords_auto_generated", [])
    for k in ["tense", "exchange", "argument", "characters"]:
        assert k in kws
    # field_confidences should reflect the higher confidence values
    fc = merged.get("field_confidences", {})
    assert fc.get("scene_summary") == 0.92
    assert fc.get("keywords_auto_generated") == 0.85
    # provenance should include both sources
    prov = merged.get("field_provenance", {})
    assert "vlm_v1" in prov.get("scene_summary", [])
    assert "vlm_v2" in prov.get("scene_summary", [])
