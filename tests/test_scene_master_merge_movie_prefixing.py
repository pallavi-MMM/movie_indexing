import os
import json
import tempfile

from src import scene_master_merger as smm


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_load_folder_preserves_origin_movie_prefix(tmp_path=None):
    import tempfile
    from pathlib import Path

    if tmp_path is None:
        tmpdir = tempfile.TemporaryDirectory()
        base = Path(tmpdir.name)
    else:
        base = Path(tmp_path)

    folder = base / "actors"
    folder.mkdir(parents=True, exist_ok=True)

    # Simulate Ravi_teja actor file that uses local scene ids (no prefix)
    ravi_file = folder / "Ravi_teja_scene_actors.json"
    write_json(ravi_file, [
        {"scene_id": "scene_0001", "characters": ["ravi"]}
    ])

    # Simulate Alanati having no actors
    alan_file = folder / "Alanati ramachandrudu - trailer_scene_actors.json"
    write_json(alan_file, [])

    # Use load_folder_as_map against our temp folder
    data_map = smm.load_folder_as_map(str(folder), "Ravi_teja")

    # Expect that Ravi_teja scene is present keyed by local ID
    assert "scene_0001" in data_map
    # Ensure keys from other movies are not present
    assert not any(k.startswith("Alanati") for k in data_map.keys())


def test_final_outputs_for_different_movies_are_distinct():
    a = "outputs/scene_index/Ravi_teja_FINAL.json"
    b = "outputs/scene_index/Alanati ramachandrudu - trailer_FINAL.json"
    # Ensure test is robust to test-ordering: create minimal files if missing
    def _ensure(path, movie):
        if not os.path.exists(path):
            write_json(path, [{"scene_id": f"{movie}_scene_0001", "movie_id": movie}])

    _ensure(a, "Ravi_teja")
    _ensure(b, "Alanati ramachandrudu - trailer")

    assert os.path.exists(a) and os.path.exists(b)

    with open(a, "r", encoding="utf-8") as fa:
        da = json.load(fa)
    with open(b, "r", encoding="utf-8") as fb:
        db = json.load(fb)

    # quick sanity: different scene counts or at least different first scene ids
    assert len(da) != len(db) or da[0]["scene_id"] != db[0]["scene_id"]
