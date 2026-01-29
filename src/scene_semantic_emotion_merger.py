"""
Semantic Emotion Merger: Merges semantic emotion data into the final complete schema.
"""

import os
import json

SEMANTIC_EMOTION_DIR = "outputs/scene_emotion"
SCENE_INDEX_DIR = "outputs/scene_index"
OUTPUT_JSON_DIR = "output_json"

os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)


def load_semantic_emotions(movie_name):
    """Load semantic emotions from file"""
    sem_file = os.path.join(
        SEMANTIC_EMOTION_DIR, f"{movie_name}_semantic_emotions.json"
    )

    if not os.path.exists(sem_file):
        return {}

    try:
        with open(sem_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("semantic_emotions", {})
    except Exception as e:
        print(f"[WARN] Could not load semantic emotions: {e}")
        return {}


def load_final_complete_schema(movie_name):
    """Load the current complete schema"""
    schema_file = os.path.join(OUTPUT_JSON_DIR, f"{movie_name}_complete_schema.json")

    if not os.path.exists(schema_file):
        return None

    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load complete schema: {e}")
        return None


def merge_semantic_emotions(complete_schema, semantic_emotions):
    """Merge semantic emotions into complete schema"""

    if not complete_schema or "scenes" not in complete_schema:
        return complete_schema

    for scene in complete_schema["scenes"]:
        scene_id = scene.get("scene_id", "")

        if scene_id in semantic_emotions:
            sem_data = semantic_emotions[scene_id]

            # Add semantic emotion fields
            scene["emotions"] = sem_data.get("emotions", [])
            scene["viewer_emotion_prediction"] = sem_data.get(
                "viewer_emotion_prediction", ""
            )
            scene["laugh_moment_flag"] = sem_data.get("laugh_moment_flag", False)
            scene["shock_moment_flag"] = sem_data.get("shock_moment_flag", False)
            scene["climax_point_flag"] = sem_data.get("climax_point_flag", False)

    # Update generated_at timestamp
    import datetime

    complete_schema["generated_at"] = datetime.datetime.now().isoformat()

    return complete_schema


def main():
    """Merge semantic emotions into complete schema"""

    # Get movie name from pipeline
    target_movie = globals().get("TARGET_MOVIE") or globals().get("MOVIE_NAME")

    # Discover movies from OUTPUT_JSON_DIR
    if not os.path.exists(OUTPUT_JSON_DIR):
        print("[INFO] No output_json directory found")
        return

    movies_found = set()
    for filename in os.listdir(OUTPUT_JSON_DIR):
        if "_complete_schema.json" in filename:
            movie_name = filename.replace("_complete_schema.json", "")
            movies_found.add(movie_name)

    # Filter to target movie if specified by pipeline
    if target_movie:
        movies_found = {target_movie}

    if not movies_found:
        print("[INFO] No complete schema files found")
        return

    for movie_name in sorted(movies_found):
        print(f"\n[SEMANTIC EMOTION MERGE] Processing: {movie_name}")

        # Load complete schema
        complete_schema = load_final_complete_schema(movie_name)
        if not complete_schema:
            print(f"[WARN] Could not load complete schema for {movie_name}")
            continue

        # Load semantic emotions
        semantic_emotions = load_semantic_emotions(movie_name)
        if not semantic_emotions:
            print(f"[WARN] No semantic emotions found for {movie_name}")
            continue

        # Merge
        merged_schema = merge_semantic_emotions(complete_schema, semantic_emotions)

        # Save
        output_file = os.path.join(
            OUTPUT_JSON_DIR, f"{movie_name}_complete_schema.json"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(merged_schema, f, indent=2, ensure_ascii=False)

        print(f"[OK] Semantic emotions merged → {output_file}")


if __name__ == "__main__":
    main()
