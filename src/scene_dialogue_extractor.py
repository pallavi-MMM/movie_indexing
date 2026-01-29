import os
import json
import math
from faster_whisper import WhisperModel
import torch

# Use central device selection (GPU when available)
from src.device import DEVICE
MODEL_SIZE = "medium"   # change to "small" if GPU memory is low
COMPUTE_TYPE = "float16" if DEVICE.startswith("cuda") else "int8"

OUT_DIR = "outputs/scene_dialogue"
os.makedirs(OUT_DIR, exist_ok=True)

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE
)


def words_per_minute(text, duration_sec):
    if duration_sec <= 0:
        return None
    words = len(text.split())
    return round((words / duration_sec) * 60, 2)


def extract_dialogue(scene_id, audio_path):
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        language="en"
    )

    dialogue = []
    full_text = []
    total_words = 0

    for seg in segments:
        line = seg.text.strip()
        if not line:
            continue
        # include timestamps when available to enable speaker alignment
        seg_start = getattr(seg, "start", None)
        seg_end = getattr(seg, "end", None)
        item = {
            "character": "",     # NOT guessed yet
            "line": line
        }
        if seg_start is not None:
            item["start"] = round(float(seg_start), 3)
        if seg_end is not None:
            item["end"] = round(float(seg_end), 3)
        dialogue.append(item)
        full_text.append(line)
        total_words += len(line.split())

    duration = info.duration if info.duration else 0
    wpm = words_per_minute(" ".join(full_text), duration)

    return {
        "scene_id": scene_id,
        "dialogue_text": dialogue,
        "dialogue_speed_wpm": wpm,
        "audio_clarity_score": round(info.language_probability, 2),
        "profanity_present": None  # filled later by dedicated filter
    }


def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    assets_dir = f"outputs/scene_assets/{movie}"
    movie_out_dir = os.path.join(OUT_DIR, movie)
    os.makedirs(movie_out_dir, exist_ok=True)

    for file in sorted(os.listdir(assets_dir)):
        if not file.endswith("_audio.wav"):
            continue

        scene_id = file.replace("_audio.wav", "")
        audio_path = os.path.join(assets_dir, file)

        print(f"[DIALOGUE] Processing {scene_id}")
        data = extract_dialogue(scene_id, audio_path)

        out_path = os.path.join(movie_out_dir, f"{scene_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    print("[OK] Dialogue extraction completed.")


if __name__ == "__main__":
    main()
