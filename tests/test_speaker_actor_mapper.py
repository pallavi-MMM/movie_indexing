from src.scene_speaker_actor_mapper import map_speakers_to_actors


def test_map_speakers_to_actors_basic():
    # Two speakers, two actors
    speaker_segments = [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0},
        {"speaker": "SPEAKER_01", "start": 1.5, "end": 3.0}
    ]
    actor_item = {
        "scene_id": "scene_0001",
        "character_dominance_ranking": [
            {"character": "Alice", "score": 100.0},
            {"character": "Bob", "score": 80.0}
        ]
    }

    mapping = map_speakers_to_actors(speaker_segments, actor_item)
    assert mapping["SPEAKER_00"] == "Alice"
    assert mapping["SPEAKER_01"] == "Bob"


def test_more_speakers_than_actors():
    speaker_segments = [
        {"speaker": "S0", "start": 0.0, "end": 0.5},
        {"speaker": "S1", "start": 0.6, "end": 1.0},
        {"speaker": "S2", "start": 1.1, "end": 1.5}
    ]
    actor_item = {
        "scene_id": "scene_0002",
        "character_dominance_ranking": [
            {"character": "Lead", "score": 100.0}
        ]
    }
    mapping = map_speakers_to_actors(speaker_segments, actor_item)
    assert mapping["S0"] == "Lead"
    assert mapping["S1"] is None or mapping["S1"] in ("Lead", None)
