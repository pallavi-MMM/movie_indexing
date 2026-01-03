from src.face_actor_pipeline import FaceActorPipeline


def test_face_actor_pipeline_maps_tracks_to_registered_actor(tmp_path):
    video = tmp_path / "movie.mp4"
    video.write_bytes(b"dummy")
    pipeline = FaceActorPipeline(dim=3, tracker_mode="mock")
    # Use a deterministic embedding equal to what the mock tracker will produce
    tracks = pipeline.tracker.track(str(video))
    assert len(tracks) >= 1
    first_emb = tracks[0]["embedding"]
    # Register an actor with the same embedding
    pipeline.register_actor("Lead", first_emb)
    chars = pipeline.process_video(str(video))
    # There should be at least one character mapped
    assert any(c["name"] == "Lead" for c in chars)
    lead = next(c for c in chars if c["name"] == "Lead")
    assert lead["screen_time"] > 0
    assert lead["confidence"] >= 0.0
