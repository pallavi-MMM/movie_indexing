"""Tests for ActorDB save/load persistence."""

import tempfile
import os
from src.actor_db import ActorDB


def test_actor_db_save_and_load():
    """Test that ActorDB can be saved and loaded from JSON."""
    # Create and populate a DB
    db = ActorDB(dim=2)
    # Use orthogonal embeddings so matching is clear
    emb1 = [1.0, 0.0]  # Alice
    emb2 = [0.0, 1.0]  # Bob
    db.add_actor("Alice", emb1, {"role": "lead"})
    db.add_actor("Bob", emb2, {"role": "supporting"})

    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        db.save(temp_path)
        assert os.path.exists(temp_path)

        # Load from temp file
        db2 = ActorDB.load(temp_path)
        assert db2.dim == 2
        assert set(db2.list_actors()) == {"Alice", "Bob"}

        # Verify embeddings and metadata are intact
        result_alice = db2.find_best(emb1)
        assert result_alice["name"] == "Alice"
        assert result_alice["matched"] is True

        result_bob = db2.find_best(emb2)
        assert result_bob["name"] == "Bob"
        assert result_bob["matched"] is True
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_actor_db_save_empty():
    """Test that an empty ActorDB can be saved and loaded."""
    db = ActorDB(dim=256)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        db.save(temp_path)
        db2 = ActorDB.load(temp_path)
        assert db2.dim == 256
        assert db2.list_actors() == []
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_actor_db_load_nonexistent_raises():
    """Test that loading a non-existent file raises FileNotFoundError."""
    try:
        ActorDB.load("/nonexistent/path/actor_db.json")
        assert False, "should have raised"
    except FileNotFoundError:
        pass
