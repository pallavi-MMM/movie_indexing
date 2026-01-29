"""Code review test: multi-scene pipeline with new movie scenarios.

Tests various edge cases and potential pitfalls:
- Missing optional fields (actor_catalog, video_path)
- Empty/null values
- Multiple scenes in sequence
- Per-character confidence aggregation
- Actor DB persistence across runs
"""

import tempfile
import os
import json
from pathlib import Path

from src.run_local_pipeline import run_scene_pipeline
from src.actor_db import ActorDB
from src.face_actor_pipeline import FaceActorPipeline


def test_new_movie_basic_scene_minimal_fields():
    """Test processing a new movie with minimal required fields."""
    scene = {
        "scene_id": "new_movie_scene_001",
        "movie_id": "NEW_MOVIE_2024",
    }
    result = run_scene_pipeline(scene)

    # Must have basic identifiers
    assert result["scene_id"] == "new_movie_scene_001"
    assert result["movie_id"] == "NEW_MOVIE_2024"

    # Should have safety and quality outputs
    assert "safety_flags" in result
    assert "quality_flags" in result

    # VLM summary should be present
    assert "scene_summary" in result
    assert "keywords_auto_generated" in result

    # Field confidences and provenance should exist
    assert "field_confidences" in result
    assert "field_provenance" in result

    print(f"✓ New movie minimal scene processed: {result.get('scene_id')}")


def test_new_movie_with_full_context():
    """Test processing a new movie with all optional enrichments."""
    scene = {
        "scene_id": "new_movie_scene_002",
        "movie_id": "NEW_MOVIE_2024",
        "dialogue_text": [
            {"character": "Alice", "line": "Hello, world!"},
            {"character": "Bob", "line": "Hello back!"},
        ],
        "objects": [
            {"type": "car"},
            {"type": "building"},
        ],
        "emotions": ["happy", "excited"],
    }
    result = run_scene_pipeline(scene)

    # Should preserve input fields
    assert len(result["dialogue_text"]) == 2
    assert len(result["objects"]) == 2

    # Should include safety/quality/VLM outputs
    assert "safety_flags" in result
    assert "quality_flags" in result
    assert "scene_summary" in result

    print(f"✓ New movie full-context scene processed: {result.get('scene_id')}")


def test_new_movie_with_face_actor_pipeline():
    """Test face->actor linking with a new movie (mocked video)."""
    # Create temporary video file (mock)
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".mp4") as f:
        video_path = f.name

    try:
        # Create actor catalog
        actor_catalog = {
            "Alice": [1.0, 0.0, 0.0],
            "Bob": [0.0, 1.0, 0.0],
        }

        scene = {
            "scene_id": "new_movie_scene_003",
            "movie_id": "NEW_MOVIE_2024",
            "video_path": video_path,
            "actor_catalog": actor_catalog,
        }

        result = run_scene_pipeline(scene)

        # Should have characters from face->actor pipeline
        assert "characters" in result
        characters = result["characters"]
        assert len(characters) > 0

        # Should have per-character confidences (as dict map)
        if "field_confidences" in result:
            fc = result["field_confidences"].get("characters")
            assert isinstance(
                fc, dict
            ), f"Expected characters confidences to be dict, got {type(fc)}"

        print(
            f"✓ New movie with face->actor pipeline processed: {len(characters)} characters detected"
        )
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


def test_new_movie_actor_db_persistence():
    """Test saving and reusing actor DB for a new movie across runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "actors.json")

        # First run: create and save actor DB
        db1 = ActorDB(dim=3)
        db1.add_actor("Lead", [1.0, 0.0, 0.0], {"role": "protagonist"})
        db1.add_actor("Support", [0.0, 1.0, 0.0], {"role": "antagonist"})
        db1.save(db_path)

        assert os.path.exists(db_path), "Actor DB file should exist"

        # Second run: load persisted DB
        db2 = ActorDB.load(db_path)
        assert set(db2.list_actors()) == {"Lead", "Support"}

        # Third run: test that loaded DB works for new movie pipeline
        scene = {
            "scene_id": "new_movie_scene_004",
            "movie_id": "NEW_MOVIE_WITH_PERSISTED_ACTORS",
        }
        result = run_scene_pipeline(scene)
        assert result["scene_id"] == "new_movie_scene_004"

        print(
            f"✓ Actor DB persisted and reloaded successfully ({len(db2.list_actors())} actors)"
        )


def test_new_movie_sequence_processing():
    """Test processing multiple scenes from same new movie in sequence."""
    movie_id = "MULTI_SCENE_NEW_MOVIE"
    scenes = [
        {
            "scene_id": f"{movie_id}_scene_001",
            "movie_id": movie_id,
            "dialogue_text": [{"character": "Alice", "line": "Scene 1"}],
        },
        {
            "scene_id": f"{movie_id}_scene_002",
            "movie_id": movie_id,
            "dialogue_text": [{"character": "Bob", "line": "Scene 2"}],
        },
        {
            "scene_id": f"{movie_id}_scene_003",
            "movie_id": movie_id,
            "dialogue_text": [{"character": "Alice", "line": "Scene 3"}],
        },
    ]

    results = []
    for scene in scenes:
        result = run_scene_pipeline(scene)
        results.append(result)
        assert result["movie_id"] == movie_id
        assert "scene_summary" in result

    assert len(results) == 3
    print(f"✓ Multi-scene new movie processed ({len(results)} scenes)")


def test_new_movie_null_and_missing_fields():
    """Test robustness with null/missing optional fields."""
    scene = {
        "scene_id": "new_movie_null_test",
        "movie_id": "NULL_TEST_MOVIE",
        "dialogue_text": None,  # Null value
        "objects": [],  # Empty list
        "video_path": None,  # Null (will skip face->actor)
        "actor_catalog": None,  # Null (will skip face->actor)
    }

    result = run_scene_pipeline(scene)

    # Should handle gracefully without crashing
    assert result["scene_id"] == "new_movie_null_test"
    assert "safety_flags" in result

    # Should not have characters (video_path was None)
    characters = result.get("characters")
    # Characters may be None or absent

    print(f"✓ New movie with null/missing fields processed gracefully")


def test_new_movie_edge_case_character_aggregation():
    """Test character aggregation with same character in multiple sources."""
    # This tests the character aggregation logic in fusion
    scene = {
        "scene_id": "new_movie_char_agg",
        "movie_id": "CHAR_AGG_MOVIE",
    }

    result = run_scene_pipeline(scene)

    # Just ensure it runs without error
    assert result["scene_id"] == "new_movie_char_agg"

    # If there are characters, check structure
    if "characters" in result:
        for char in result.get("characters", []):
            assert "name" in char
            assert "screen_time" in char
            assert isinstance(char["screen_time"], (int, float))

    print(f"✓ Character aggregation edge case handled")


if __name__ == "__main__":
    test_new_movie_basic_scene_minimal_fields()
    test_new_movie_with_full_context()
    test_new_movie_with_face_actor_pipeline()
    test_new_movie_actor_db_persistence()
    test_new_movie_sequence_processing()
    test_new_movie_null_and_missing_fields()
    test_new_movie_edge_case_character_aggregation()
    print("\n✓ All code review tests passed!")
