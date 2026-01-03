from src.face_tracker import FaceTracker
from src.actor_linker import ActorLinker


def test_integration_track_matches_actor(tmp_path):
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"video")
    ft = FaceTracker(mode="mock")
    tracks = ft.track(str(video))
    assert len(tracks) >= 1
    # Build linker with an actor that matches the first track's embedding
    first_emb = tracks[0]["embedding"]
    al = ActorLinker(mode="mock")
    al.add_actor("Lead", first_emb)
    res = al.match_embedding(first_emb, threshold=0.5)
    assert res["matched"] is True
    assert res["name"] == "Lead"
