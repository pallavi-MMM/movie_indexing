import os
import json

# ---------------- CONFIG ----------------

SEGMENTS_DIR = "outputs/scenes"
ACTORS_DIR = "outputs/scene_actor_index"
ASSETS_DIR = "outputs/scene_assets"
OUTPUT_DIR = "outputs/scene_index"


# ---------------- HELPERS ----------------

def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------- CORE LOGIC ----------------

def build_movie_json(movie_id):
    print("RUNNING FILE:", __file__)
    print("Building scene JSON for movie:", movie_id)

    # ---- Load inputs ----
    segments = load_json(f"{SEGMENTS_DIR}/{movie_id}_scenes.json")
    # Actor file may be missing or empty — treat missing as [] for robustness
    actor_path = f"{ACTORS_DIR}/{movie_id}_scene_actors.json"
    try:
        actor_data = load_json(actor_path)
    except FileNotFoundError:
        print(f"[WARN] Actor file not found: {actor_path} — proceeding with empty actor list")
        actor_data = []

    # ---- Validate scene schema ----
    if not isinstance(segments, dict):
        raise TypeError(f"Segments must be dict, got {type(segments)}")

    if "scenes" not in segments:
        raise KeyError("Expected key 'scenes' in segments JSON")

    scene_list = segments["scenes"]

    if not isinstance(scene_list, list):
        raise TypeError(f"'scenes' must be list, got {type(scene_list)}")

    print(f"Detected {len(scene_list)} scenes")

    # ---- Validate actor schema ----
    if not isinstance(actor_data, list):
        raise TypeError(f"Actor data must be list, got {type(actor_data)}")

    # Accept both local scene ids and prefixed ids (backwards compatibility)
    actor_map = {}
    for s in actor_data:
        sid = s.get("scene_id")
        if not sid:
            continue
        actor_map[sid] = s
        actor_map[f"{movie_id}_{sid}"] = s

    scenes_out = []

    # ---- Build final scene objects ----
    for idx, seg in enumerate(scene_list, start=1):

        if not isinstance(seg, dict):
            raise TypeError(f"Scene {idx} is not dict, got {type(seg)}")

        scene_id = f"{movie_id}_scene_{idx:04d}"
        asset_scene_dir = f"{ASSETS_DIR}/{movie_id}/scene_{idx:04d}"

        scene_json = {
            "scene_id": scene_id,

            "start_time": seg.get("start_time"),
            "end_time": seg.get("end_time"),
            "duration": seg.get("duration"),

            "transition_type": seg.get("transition_type"),
            "transition_confidence": seg.get("transition_confidence"),

            "scene_summary": "",
            "scene_type": "",
            "importance_score": 0,

            "characters": actor_map
                .get(scene_id, {})
                .get("characters", []),

            "character_dominance_ranking": actor_map
                .get(scene_id, {})
                .get("character_dominance_ranking", []),

            "assets": {
                "frames_dir": f"{asset_scene_dir}/frames",
                "audio_dir": f"{asset_scene_dir}/audio"
            }
        }

        scenes_out.append(scene_json)

    # ---- Save output ----
    out_path = f"{OUTPUT_DIR}/{movie_id}_scenes_final.json"
    save_json(scenes_out, out_path)

    print(f"✅ Scene JSON written: {out_path}")
    print("Total scenes:", len(scenes_out))


# ---------------- ENTRY ----------------

def main():
    movie_id = "Ravi_teja"  # change as needed
    build_movie_json(movie_id)


if __name__ == "__main__":
    main()
