from src.visual_quality import analyze_visual_quality


def test_honors_explicit_black_and_flash_flags():
    scene = {
        "scene_id": "s1",
        "movie_id": "m1",
        "black_frames_detected": True,
        "flash_frames_detected": False,
    }
    out = analyze_visual_quality(scene)
    assert out["quality_flags"]["black_frames_detected"] is True
    assert out["field_confidences"]["black_frames_detected"] >= 0.9
    assert out["quality_flags"]["flash_frames_detected"] is False


def test_bitrate_low_flags_drop_and_high_no_drop():
    s_low = {"scene_id": "s2", "movie_id": "m1", "bitrate": 300}
    out_low = analyze_visual_quality(s_low)
    assert out_low["quality_flags"]["bitrate_drop_detected"] is True
    assert out_low["field_confidences"]["bitrate_drop_detected"] >= 0.8

    s_high = {"scene_id": "s3", "movie_id": "m1", "bitrate": 1200}
    out_high = analyze_visual_quality(s_high)
    assert out_high["quality_flags"]["bitrate_drop_detected"] is False
    assert out_high["field_confidences"]["bitrate_drop_detected"] >= 0.7


def test_defaults_to_low_confidence_when_absent():
    s = {"scene_id": "s4", "movie_id": "m1"}
    out = analyze_visual_quality(s)
    assert out["quality_flags"]["black_frames_detected"] is False
    assert out["field_confidences"]["black_frames_detected"] == 0.1
