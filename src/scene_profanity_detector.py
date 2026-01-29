import os
import json
import re

INPUT_JSON = None
OUTPUT_JSON = None

# Conservative profanity list (extend carefully)
PROFANITY_WORDS = {
    "fuck", "fucking", "shit", "bitch", "bastard",
    "asshole", "damn", "bloody"
}

def normalize(text):
    return re.sub(r"[^a-zA-Z\s]", "", text.lower())

def contains_profanity(dialogue_lines):
    for d in dialogue_lines:
        line = normalize(d.get("line", ""))
        words = set(line.split())
        if words & PROFANITY_WORDS:
            return True
    return False

def main():
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])
    input_json = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE.json"
    output_json = f"outputs/scene_index/{movie}_FINAL_WITH_DIALOGUE_PROFANITY.json"

    scenes = None
    if os.path.exists(input_json):
        with open(input_json, "r", encoding="utf-8") as f:
            scenes = json.load(f)
    else:
        # fallback: assemble scenes from per-scene dialogue files
        dialogue_dir = os.path.join("outputs", "scene_dialogue", movie)
        if not os.path.exists(dialogue_dir):
            print(f"[WARN] Profanity detector: no input found for {movie}, skipping")
            return
        scenes = []
        for fn in sorted(os.listdir(dialogue_dir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(dialogue_dir, fn), "r", encoding="utf-8") as f:
                d = json.load(f)
            scenes.append(d)

    for scene in scenes:
        dialogue = scene.get("dialogue_text", [])
        if not dialogue:
            scene["profanity_present"] = None
            continue

        detected = contains_profanity(dialogue)
        scene["profanity_present"] = bool(detected)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[OK] Profanity detection complete → {output_json}")

if __name__ == "__main__":
    main()
