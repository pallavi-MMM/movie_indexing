from src.scene_schema import validate_scene


def test_field_confidences_accepts_per_item_map():
    scene = {
        "scene_id": "s1",
        "movie_id": "m1",
        "field_confidences": {"characters": {"Alice": 0.9, "Bob": 0.8}},
    }
    valid, msgs = validate_scene(scene)
    assert valid, msgs
