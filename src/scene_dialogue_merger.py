import json
import os

DIALOGUE_DIR = "outputs/scene_dialogue"


def load_dialogue_data(movie_name: str):
    dialogue_map = {}
    movie_dir = os.path.join(DIALOGUE_DIR, movie_name)
    if not os.path.exists(movie_dir):
        return dialogue_map

    for file in os.listdir(movie_dir):
        if not file.endswith(".json"):
            continue
        path = os.path.join(movie_dir, file)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            dialogue_map[data["scene_id"]] = data

    return dialogue_map


def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    master_json = f"outputs/scene_index/{movie}_FINAL.json"
    scenes = None

    if os.path.exists(master_json):
        with open(master_json, "r", encoding="utf-8") as f:
            scenes = json.load(f)
    else:
        # fallback: build minimal scene list from segments file
        segments_path = os.path.join("outputs", "scenes", f"{movie}_scenes.json")
        if not os.path.exists(segments_path):
            print(f"[WARN] Dialogue merger: no master or scenes file found for {movie}, skipping")
            return
        with open(segments_path, "r", encoding="utf-8") as f:
            segs = json.load(f).get("scenes", [])
        scenes = []
        for s in segs:
            scenes.append({
                "scene_id": s.get("scene_id"),
                "start_time": s.get("start_time"),
                "end_time": s.get("end_time"),
                "duration": s.get("duration"),
            })

    dialogue_data = load_dialogue_data(movie)

    for scene in scenes:
        sid = scene["scene_id"]
        if sid in dialogue_data:
            d = dialogue_data[sid]

            scene["dialogue_text"] = d.get("dialogue_text", [])
            scene["dialogue_speed_wpm"] = d.get("dialogue_speed_wpm")
            scene["audio_clarity_score"] = d.get("audio_clarity_score")
            scene["profanity_present"] = d.get("profanity_present")

    output_json = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[OK] Dialogue merged → {output_json}")


if __name__ == "__main__":
    main()
