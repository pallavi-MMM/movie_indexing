from src.scene_schema import validate_scene


def test_objects_must_be_object_dicts():
    # objects should be list of object dicts with 'type' key per canonical schema
    scene = {
        "scene_id": "scene_0001",
        "movie_id": "M1",
        "objects": ["person", "car"]
    }

    valid, msgs = validate_scene(scene)
    assert not valid
    # expecting a message indicating array items invalid or type mismatch
    assert any("objects" in m or "field objects" in m or "is not of type" in m for m in msgs)
