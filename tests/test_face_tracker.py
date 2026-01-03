from src.face_tracker import FaceTracker


def test_mock_tracking_returns_expected_structure(tmp_path):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"fake video")
    ft = FaceTracker(mode="mock")
    tracks = ft.track(str(video))
    assert isinstance(tracks, list)
    assert len(tracks) >= 1
    for tr in tracks:
        assert "track_id" in tr and isinstance(tr["track_id"], int)
        assert "frames" in tr and isinstance(tr["frames"], list)
        assert "embedding" in tr and isinstance(tr["embedding"], list)
        for f in tr["frames"]:
            assert "ts" in f and isinstance(f["ts"], float)
            assert "bbox" in f and len(f["bbox"]) == 4


def test_auto_mode_falls_back_to_mock_when_no_backend(tmp_path):
    video = tmp_path / "sample2.mp4"
    video.write_bytes(b"fake")
    ft = FaceTracker(mode="auto")
    tracks = ft.track(str(video))
    # Accept either a real backend or the mock structure; ensure structure is present
    assert isinstance(tracks, list)
    assert len(tracks) >= 1
