import os
import json

from src.phase_i import scene_json_builder as builder


def write_segments(movie_id):
    path = os.path.join("outputs", "scenes", f"{movie_id}_scenes.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    segs = {
        "scenes": [
            {
                "scene_id": "scene_0001",
                "start_time": "00:00:00.000",
                "end_time": "00:00:05.000",
                "duration": 5,
            }
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(segs, f)


def test_actor_merge_happy_path(tmp_path, monkeypatch):
    movie = "TEST_MOVIE"
    write_segments(movie)

    # actor file with local scene_id
    actor = [
        {
            "scene_id": "scene_0001",
            "characters": ["Alice"],
            "character_dominance_ranking": [{"character": "Alice", "score": 1.0}],
        }
    ]
    os.makedirs("outputs/scene_actor_index", exist_ok=True)
    with open(
        f"outputs/scene_actor_index/{movie}_scene_actors.json", "w", encoding="utf-8"
    ) as f:
        json.dump(actor, f)

    builder.build_movie_json(movie)
    out = json.load(
        open(f"outputs/scene_index/{movie}_scenes_final.json", "r", encoding="utf-8")
    )
    assert out[0]["characters"] == ["Alice"]
    assert out[0]["character_dominance_ranking"][0]["character"] == "Alice"


def test_actor_missing_or_empty(tmp_path):
    movie = "TEST_MOVIE2"
    write_segments(movie)
    # Ensure actor file missing
    path = f"outputs/scene_actor_index/{movie}_scene_actors.json"
    if os.path.exists(path):
        os.remove(path)

    builder.build_movie_json(movie)  # should not raise
    out = json.load(
        open(f"outputs/scene_index/{movie}_scenes_final.json", "r", encoding="utf-8")
    )
    assert out[0]["characters"] == []
    assert out[0]["character_dominance_ranking"] == []
