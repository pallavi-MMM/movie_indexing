from src.run_local_pipeline import run_scene_pipeline
from src.face_tracker import FaceTracker


def test_pipeline_includes_characters_from_face_actor(tmp_path):
    # create fake video file
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"dummy video")

    # Use FaceTracker to get deterministic mock embedding for the test
    ft = FaceTracker(mode="mock")
    tracks = ft.track(str(video))
    assert len(tracks) >= 1
    emb = tracks[0]["embedding"]

    scene = {
        "scene_id": "s_face1",
        "movie_id": "m1",
        "video_path": str(video),
        # register actor matching the first track embedding
        "actor_catalog": {"Lead": emb},
    }

    merged = run_scene_pipeline(scene)
    # merged should include characters; they may be present under `characters`
    chars = merged.get("characters", [])
    assert isinstance(chars, list)
    # there should be an entry for Lead (registered actor)
    assert any((c.get("name") == "Lead") for c in chars)
