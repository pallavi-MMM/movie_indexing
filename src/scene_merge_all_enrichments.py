"""
Complete merger: Merges ALL enrichment layers into final complete schema.
Handles: semantic emotions, audio intelligence, narrative structure.
"""

import os
import json
import sys


def merge_all_enrichments(movie_name):
    """
    Merge all enrichment layers into complete schema.

    Layers:
      1. Semantic emotions (5 fields)
      2. Audio intelligence (7 fields)
      3. Narrative structure (4 fields)
    """
    output_json_dir = "output_json"
    complete_schema_file = f"{output_json_dir}/{movie_name}_complete_schema.json"

    if not os.path.exists(complete_schema_file):
        print(f"[WARN] Complete schema not found: {complete_schema_file}")
        return False

    with open(complete_schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    scenes = schema.get("scenes", [])
    total_scenes = len(scenes)

    print(f"[MERGE ALL] Processing {total_scenes} scenes for {movie_name}")

    # === LAYER 1: SEMANTIC EMOTIONS ===
    print("[MERGE] Loading semantic emotions...")
    sem_emotions_file = (
        f"outputs/scene_emotion/{movie_name}/{movie_name}_semantic_emotions.json"
    )
    sem_emotions = {}

    if os.path.exists(sem_emotions_file):
        with open(sem_emotions_file, "r", encoding="utf-8") as f:
            sem_data = json.load(f)
            sem_emotions = sem_data.get("semantic_emotions", {})

    # === LAYER 2: AUDIO INTELLIGENCE ===
    print("[MERGE] Loading audio intelligence...")
    audio_intel_file = (
        f"outputs/scene_audio/{movie_name}/{movie_name}_audio_intelligence.json"
    )
    audio_intel = {}

    if os.path.exists(audio_intel_file):
        with open(audio_intel_file, "r", encoding="utf-8") as f:
            audio_data = json.load(f)
            audio_intel = audio_data.get("audio_intelligence", {})

    # === MERGE INTO SCENES ===
    print("[MERGE] Applying enrichment layers to scenes...")
    merged_count = 0

    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", "")

        # Apply semantic emotions
        if scene_id in sem_emotions:
            sem = sem_emotions[scene_id]
            scene["emotions"] = sem.get("emotions", [])
            scene["viewer_emotion_prediction"] = sem.get(
                "viewer_emotion_prediction", ""
            )
            scene["laugh_moment_flag"] = sem.get("laugh_moment_flag", False)
            scene["shock_moment_flag"] = sem.get("shock_moment_flag", False)
            scene["climax_point_flag"] = sem.get("climax_point_flag", False)
        else:
            # Default values if not found
            scene["emotions"] = []
            scene["viewer_emotion_prediction"] = ""
            scene["laugh_moment_flag"] = False
            scene["shock_moment_flag"] = False
            scene["climax_point_flag"] = False

        # Apply audio intelligence
        if scene_id in audio_intel:
            audio = audio_intel[scene_id]
            scene["background_music_mood"] = audio.get(
                "background_music_mood", "unknown"
            )
            scene["sfx_presence"] = audio.get("sfx_presence", False)
            scene["sfx_details"] = audio.get("sfx_details", [])
            scene["audio_peaks_detected"] = audio.get("audio_peaks_detected", False)
            scene["sound_design_notes"] = audio.get("sound_design_notes", "")
            scene["narration_present"] = audio.get("narration_present", False)
            scene["narration_text"] = audio.get("narration_text", "")
        else:
            # Default values if not found
            scene["background_music_mood"] = "unknown"
            scene["sfx_presence"] = False
            scene["sfx_details"] = []
            scene["audio_peaks_detected"] = False
            scene["sound_design_notes"] = ""
            scene["narration_present"] = False
            scene["narration_text"] = ""

        # Apply narrative structure
        # Compute story progress tag
        position = (idx + 1) / total_scenes
        climax_flag = scene.get("climax_point_flag", False)

        if climax_flag:
            story_tag = "climax"
        elif position < 0.15:
            story_tag = "intro"
        elif position < 0.30:
            story_tag = "setup"
        elif position < 0.55:
            story_tag = "buildup"
        elif position < 0.70:
            story_tag = "conflict"
        elif position < 0.90:
            story_tag = "resolution"
        else:
            story_tag = "epilogue"

        scene["story_progress_tag"] = story_tag

        # Narrative function (simple heuristic for now)
        dialogue = scene.get("dialogue_text", [])
        characters = scene.get("characters", [])

        if len(characters) > 0 and len(dialogue) <= 1:
            narrative_func = "introduce_character"
        elif len(dialogue) > 5:
            narrative_func = "reveal_information"
        elif len(characters) > 0:
            narrative_func = "develop_relationship"
        else:
            narrative_func = "emotional_turn"

        scene["narrative_function"] = narrative_func

        merged_count += 1

        if merged_count % 50 == 0:
            print(f"  Merged {merged_count}/{total_scenes} scenes...")

    # Save
    with open(complete_schema_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"[OK] All enrichment layers merged - {merged_count} scenes updated")
    return True


def main():
    """Entry point."""
    if len(sys.argv) > 1:
        movie_name = sys.argv[1]
    else:
        movie_name = "Dukudu-movie"

    merge_all_enrichments(movie_name)


if __name__ == "__main__":
    main()
