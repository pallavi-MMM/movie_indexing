import os
import json

# INPUTS
EMOTION_DIR = "outputs/scene_emotion"


def load_emotion_data(movie_name: str):
    emotion_map = {}

    movie_dir = os.path.join(EMOTION_DIR, movie_name)
    if not os.path.exists(movie_dir):
        return emotion_map

    for file in os.listdir(movie_dir):
        if not file.endswith(".json"):
            continue

        path = os.path.join(movie_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            emotion_map[data["scene_id"]] = data

    return emotion_map


def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    master_json = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_PROFANITY.json"

    scenes = None
    # prefer profanity-augmented master, fall back to dialogue-augmented or base master
    candidates = [
        f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_PROFANITY.json",
        f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE.json",
        f"outputs/scene_index/{movie}_FINAL.json",
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                scenes = json.load(f)
            break

    if scenes is None:
        # fallback: if segments exist, build minimal scene list (no dialogue/profanity)
        segs = os.path.join("outputs", "scenes", f"{movie}_scenes.json")
        if not os.path.exists(segs):
            print(f"[WARN] Emotion merger: no input found for {movie}, skipping")
            return
        with open(segs, "r", encoding="utf-8") as f:
            segs_json = json.load(f).get("scenes", [])
        scenes = [{"scene_id": s.get("scene_id")} for s in segs_json]

    emotion_data = load_emotion_data(movie)

    for scene in scenes:
        sid = scene["scene_id"]

        if sid not in emotion_data:
            continue

        e = emotion_data[sid]

        # Conservative merge: numeric signals only
        scene["emotion_arousal_score"] = e.get("emotion_arousal_score")
        scene["emotion_scene_variation_score"] = e.get("emotion_scene_variation_score")

        # Optional helper (not in original schema but allowed)
        scene["audio_activity_score"] = e.get("audio_activity_score")

    output_json = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_EMOTION.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[OK] Emotion merged → {output_json}")


if __name__ == "__main__":
    main()
