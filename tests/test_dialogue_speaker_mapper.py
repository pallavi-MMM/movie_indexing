import json
from src.scene_dialogue_speaker_mapper import assign_speakers_to_dialogue


def test_assign_speakers_basic_overlap():
    dialogue = [
        {"line": "Hello", "start": 0.0, "end": 1.2, "character": ""},
        {"line": "Hi", "start": 1.3, "end": 2.0, "character": ""},
        {"line": "Goodbye", "start": 2.5, "end": 3.0, "character": ""},
    ]

    speakers = [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.5},
        {"speaker": "SPEAKER_01", "start": 1.5, "end": 3.5},
    ]

    mapped = assign_speakers_to_dialogue(dialogue, speakers)
    assert mapped[0]["character"] == "SPEAKER_00"
    assert mapped[1]["character"] == "SPEAKER_01"
    assert mapped[2]["character"] == "SPEAKER_01"


def test_assign_speakers_no_overlap_sets_none():
    dialogue = [{"line": "Orphan line", "start": 10.0, "end": 11.0, "character": ""}]
    speakers = [{"speaker": "S0", "start": 0.0, "end": 1.0}]
    mapped = assign_speakers_to_dialogue(dialogue, speakers)
    assert mapped[0]["character"] is None
