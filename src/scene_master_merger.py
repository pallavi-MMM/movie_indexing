import os
import json
from datetime import datetime



def load_scene_timings(movie_name):
    path = f"outputs/scenes/{movie_name}_scenes.json"

    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    timing_map = {}

    for scene in data.get("scenes", []):
        # key by local scene id (e.g., 'scene_0001') to avoid cross-movie prefixes
        sid = scene.get("scene_id")
        timing_map[sid] = {
            "start_time": scene.get("start_time"),
            "end_time": scene.get("end_time"),
            "duration": scene.get("duration"),
        }

    return timing_map


# ================= CONFIG =================

BASE_DIR = "outputs"

SCENE_SEGMENTS = f"{BASE_DIR}/scene_segments"
SCENE_ACTORS = f"{BASE_DIR}/scene_actor_index"
SCENE_VISUAL = f"{BASE_DIR}/scene_visual_index"
SCENE_OBJECTS = f"{BASE_DIR}/scene_object_index"
SCENE_CONTEXT = f"{BASE_DIR}/scene_context_index"
SCENE_DIALOGUE = f"{BASE_DIR}/scene_dialogue"
SCENE_EMOTION = f"{BASE_DIR}/scene_emotion"
SCENE_SPEAKERS = f"{BASE_DIR}/scene_speakers"

OUT_DIR = f"{BASE_DIR}/scene_index"
FINAL_OUTPUT_DIR = "output_json"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)

# ================= HELPERS =================

def normalize_scene_id(scene_id: str, movie: str) -> str:
    """Ensure scene_id is prefixed with movie name"""
    if scene_id.startswith(movie):
        return scene_id
    return f"{movie}_{scene_id}"


def load_folder_as_map(folder_path, movie_name: str):
    """
    Loads JSON files from a folder.
    Supports:
      - single dict JSON
      - list of dicts JSON
      - nested movie folders (outputs/scene_dialogue/{movie}/)
    Returns: { scene_id : data }
    """
    data_map = {}

    if not os.path.exists(folder_path):
        return data_map

    # Check if folder has movie-specific subfolders (like scene_dialogue, scene_emotion)
    movie_subfolder = os.path.join(folder_path, movie_name)
    search_folder = movie_subfolder if os.path.exists(movie_subfolder) else folder_path

    for file in os.listdir(search_folder):
        if not file.endswith(".json"):
            continue

        path = os.path.join(search_folder, file)
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)

            # Determine origin movie for this file (filename prefix or content)
            stem = os.path.splitext(file)[0]
            file_movie = None
            if "_scene_" in stem:
                file_movie = stem.split("_scene_")[0]
            # content may contain movie_id
            if isinstance(content, dict) and content.get("movie_id"):
                file_movie = content.get("movie_id")
            if isinstance(content, list) and content and isinstance(content[0], dict) and content[0].get("movie_id"):
                file_movie = content[0].get("movie_id")

            # Only include items that belong to the requested movie
            def local_sid(raw_sid: str) -> str:
                # strip any movie prefix if present
                if "_" in raw_sid and raw_sid.count("_") >= 2 and raw_sid.split("_")[0] == file_movie:
                    # raw_sid like '<movie>_scene_0001' -> return 'scene_0001'
                    parts = raw_sid.split("_", 1)
                    return parts[1]
                return raw_sid

            if isinstance(content, list):
                for item in content:
                    sid = item.get("scene_id")
                    if not sid:
                        continue
                    # if file_movie is known and doesn't match requested movie_name -> skip
                    if file_movie and file_movie != movie_name:
                        continue
                    # otherwise accept item if either file_movie is None (assume it's for requested movie)
                    sid_local = local_sid(sid)
                    data_map[sid_local] = item

            elif isinstance(content, dict):
                sid = content.get("scene_id")
                if not sid:
                    continue
                if file_movie and file_movie != movie_name:
                    continue
                sid_local = local_sid(sid)
                data_map[sid_local] = content

    return data_map


def empty_scene_template(scene_id):
    return {
        "scene_id": scene_id,
        "movie_id": None,
        "title_name": None,

        "start_time": None,
        "end_time": None,
        "duration": None,

        "scene_summary": "",
        "scene_type": "",
        "scene_category_secondary": "",

        "importance_score": None,
        "scene_priority": "",
        "scene_priority_score": None,
        "viewer_attention_score": None,
        "key_plot_point": None,

        "characters": [],
        "character_dominance_ranking": [],

        "dialogue_text": [],
        "dialogue_speed_wpm": None,
        "audio_clarity_score": None,
        "profanity_present": None,

        "location": "",
        "time_of_day": "",
        "indoor_outdoor": "",

        "objects": [],
        "actions": [],
        "background_activity": [],

        "resolution": "",
        "aspect_ratio": None,
        "motion_intensity_score": None,
        "camera_movement": "",
        "lighting_style": "",
        "color_tone": "",
        "shot_type": "",

        "emotion_arousal_score": None,
        "emotion_scene_variation_score": None,
        "audio_activity_score": None,

        "vfx_presence": None,
        "cg_characters_present": None,

        "ai_confidence_score": None,
        "ai_model_version": "",
        "metadata_generated_at": datetime.utcnow().isoformat(),
        "notes": ""
    }


def merge_scene(target: dict, src: dict, src_name: str = None):
    """Deterministic merge helper.

    Current behavior mirrors the old `dict.update()` (latest wins) to avoid
    changing existing outputs. This helper centralizes merging so we can
    add per-field rules in the future without touching the main loop.
    """
    # conservative rules:
    # - do not overwrite scene_id or movie_id
    # - lists: if target empty -> set; else append missing items (preserve target order)
    # - strings: if target empty/None -> set; else keep existing
    # - numbers/bools: if target is None -> set; else keep existing
    # - dicts: shallow-merge preferring existing keys
    for k, v in src.items():
        if k in ("scene_id", "movie_id"):
            continue

        existing = target.get(k, None)

        # lists -> union-preserve-order (append items from src not present in target)
        if isinstance(v, list):
            if not existing:
                target[k] = v
            else:
                # avoid duplicates (primitive and dict by string repr)
                seen = set()
                out = []
                def key_of(item):
                    if isinstance(item, dict):
                        return json.dumps(item, sort_keys=True)
                    return str(item)

                for item in existing:
                    seen.add(key_of(item))
                    out.append(item)
                for item in v:
                    kitem = key_of(item)
                    if kitem not in seen:
                        seen.add(kitem)
                        out.append(item)
                target[k] = out

        # dicts -> shallow merge: keep existing keys, add missing
        elif isinstance(v, dict):
            if not existing:
                target[k] = v
            else:
                merged = dict(existing)
                for subk, subv in v.items():
                    if subk not in merged or merged[subk] is None:
                        merged[subk] = subv
                target[k] = merged

        # strings: set only if existing empty or None
        elif isinstance(v, str):
            if not existing:
                target[k] = v

        # numbers / bools: set if existing is None
        elif isinstance(v, (int, float, bool)):
            if existing is None:
                target[k] = v

        else:
            # fallback: set if missing
            if k not in target:
                target[k] = v

    return target

# ================= MAIN =================

def main():
    # Determine which movie to process (TARGET_MOVIE set by orchestrator, else module-level MOVIE_NAME)
    import sys
    from src.movie_utils import resolve_movie

    movie = resolve_movie(sys.modules[__name__])

    print(f"[INFO] Loading per-phase data for movie: {movie}")

    segments = load_folder_as_map(SCENE_SEGMENTS, movie)
    actors = load_folder_as_map(SCENE_ACTORS, movie)
    visuals = load_folder_as_map(SCENE_VISUAL, movie)
    objects = load_folder_as_map(SCENE_OBJECTS, movie)
    context = load_folder_as_map(SCENE_CONTEXT, movie)
    dialogue = load_folder_as_map(SCENE_DIALOGUE, movie)
    emotion = load_folder_as_map(SCENE_EMOTION, movie)
    speakers = load_folder_as_map(SCENE_SPEAKERS, movie)
    scene_timings = load_scene_timings(movie)

    # Debug: report per-source item counts for this movie to aid diagnosis
    sources = {
        "segments": segments,
        "actors": actors,
        "visuals": visuals,
        "objects": objects,
        "context": context,
        "dialogue": dialogue,
        "emotion": emotion,
        "speakers": speakers,
    }
    for name, src in sources.items():
        if not src:
            print(f"[WARN] No data found for source '{name}' for movie '{movie}'")
        else:
            print(f"[INFO] Source '{name}' contains {len(src)} scene entries for movie '{movie}'")

    # canonical scene ids come from the scenes JSON for this movie (local ids)
    scene_ids = sorted(scene_timings.keys())
    final_scenes = []

    for local_sid in scene_ids:
        scene = empty_scene_template(local_sid)

        # add timing info if available
        if local_sid in scene_timings:
            scene.update(scene_timings[local_sid])

        # conservative merges from phase outputs (only local scene ids)
        for source_name, source in (("segments", segments), ("actors", actors), ("visuals", visuals), ("objects", objects), ("context", context), ("dialogue", dialogue), ("emotion", emotion), ("speakers", speakers)):
            if local_sid in source:
                merge_scene(scene, source[local_sid], src_name=source_name)

        # ensure movie_id/title_name are set correctly for this run
        scene["movie_id"] = movie
        scene["title_name"] = movie

        final_scenes.append(scene)

    # write provenance alongside final JSON (non-invasive)
    provenance = {}
    for s in final_scenes:
        pid = s["scene_id"]
        # minimal provenance: record which fields are present in the merged scene
        prov = {}
        for field, val in s.items():
            if field in ("scene_id", "movie_id", "title_name"):
                continue
            if val not in (None, "", [], {}):
                prov[field] = True
        provenance[pid] = prov


    # compute output paths for this movie
    out_dir = OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    output_file = f"{out_dir}/{movie}_FINAL.json"
    provenance_file = f"{out_dir}/{movie}_FINAL.provenance.json"
    
    # final complete schema output path
    final_output_file = f"{FINAL_OUTPUT_DIR}/{movie}_complete_schema.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_scenes, f, indent=2, ensure_ascii=False)

    with open(provenance_file, "w", encoding="utf-8") as pf:
        json.dump(provenance, pf, indent=2, ensure_ascii=False)
    
    # save final complete schema to output_json folder
    with open(final_output_file, "w", encoding="utf-8") as f:
        json.dump({
            "movie": movie,
            "total_scenes": len(final_scenes),
            "scenes": final_scenes,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)

    print(f"[OK] Final master JSON written → {output_file}")
    print(f"[OK] Complete schema saved → {final_output_file}")
    print(f"[OK] Total scenes merged: {len(final_scenes)}")

    # Final schema check: warn or fail depending on environment
    try:
        from src.scene_schema import validate_scene
        strict = __import__("os").getenv("SCHEMA_STRICT", "0").lower() in ("1", "true", "yes")
        for s in final_scenes:
            valid, msgs = validate_scene(s)
            if not valid:
                if strict:
                    raise RuntimeError(f"Schema validation failed for scene {s.get('scene_id')}: {msgs}")
                else:
                    print(f"[WARN] Schema issue in scene {s.get('scene_id')}: {msgs}")
    except Exception:
        # non-fatal: don't break pipeline when validator import unexpectedly fails
        pass


if __name__ == "__main__":
    main()
